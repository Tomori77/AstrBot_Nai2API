"""
Cloudflare R2 上传器

通过 S3 协议上传图片到 R2，并按数量上限清理最旧图片。
命名规则: {简称}{YY}{MM}{DD}{HH}{mm}.{ext}
"""

import asyncio
import time
from datetime import datetime
from urllib.parse import quote

import aioboto3
from botocore.config import Config as BotoConfig

from astrbot.api import logger

from .image_manager import _guess_ext


class R2Uploader:
    """Cloudflare R2 S3 上传 + 清理"""

    def __init__(
        self,
        access_key_id: str,
        secret_access_key: str,
        s3_endpoint: str,
        bucket: str,
        public_base_url: str,
        storage_prefix: str = "qbotimage",
        max_cached: int = 30,
    ):
        self._access_key_id = access_key_id.strip()
        self._secret_access_key = secret_access_key.strip()
        self._s3_endpoint = s3_endpoint.strip().rstrip("/")
        self._bucket = bucket.strip()
        self._public_base_url = public_base_url.strip().rstrip("/")
        self._prefix = storage_prefix.strip().strip("/")
        self._max_cached = int(max_cached)

    def is_configured(self) -> bool:
        """判断 R2 凭证是否齐全"""
        return all([
            self._access_key_id,
            self._secret_access_key,
            self._s3_endpoint,
            self._bucket,
            self._public_base_url,
        ])

    def _build_object_key(self, short_name: str, ext: str) -> str:
        """构造对象 key: qbotimage/猫娘2606221053.png"""
        ts = datetime.now().strftime("%y%m%d%H%M")
        safe_name = quote(f"{short_name}{ts}.{ext}", safe="")
        return f"{self._prefix}/{safe_name}"

    def _build_public_url(self, object_key: str) -> str:
        """构造公开访问 URL"""
        return f"{self._public_base_url}/{object_key}"

    async def upload(self, data: bytes, short_name: str) -> str:
        """
        上传图片到 R2。

        Args:
            data: 图片二进制
            short_name: 简称（如 猫娘）

        Returns:
            公开访问 URL
        """
        if not self.is_configured():
            raise RuntimeError("R2 未配置完整凭证")

        ext = _guess_ext(data)
        object_key = self._build_object_key(short_name, ext)
        url = self._build_public_url(object_key)

        session = aioboto3.Session()
        t_start = time.perf_counter()

        try:
            async with session.client(
                "s3",
                endpoint_url=self._s3_endpoint,
                aws_access_key_id=self._access_key_id,
                aws_secret_access_key=self._secret_access_key,
                config=BotoConfig(
                    signature_version="s3v4",
                    retries={"max_attempts": 3, "mode": "standard"},
                ),
                region_name="auto",
            ) as s3:
                await s3.put_object(
                    Bucket=self._bucket,
                    Key=object_key,
                    Body=data,
                    ContentType=f"image/{ext}",
                )

            elapsed = time.perf_counter() - t_start
            logger.info(
                "[R2Uploader] 上传成功: %s, %.2fs, %d bytes",
                object_key, elapsed, len(data),
            )
            return url

        except Exception as e:
            logger.error("[R2Uploader] 上传失败: %s", e)
            raise RuntimeError(f"R2 上传失败: {e}") from e

    async def cleanup(self) -> None:
        """清理 R2 旧图片，保留 max_cached 张（按 LastModified 删最旧）"""
        if self._max_cached <= 0:
            return

        session = aioboto3.Session()
        try:
            async with session.client(
                "s3",
                endpoint_url=self._s3_endpoint,
                aws_access_key_id=self._access_key_id,
                aws_secret_access_key=self._secret_access_key,
                config=BotoConfig(signature_version="s3v4"),
                region_name="auto",
            ) as s3:
                listing = await s3.list_objects_v2(
                    Bucket=self._bucket,
                    Prefix=f"{self._prefix}/",
                )

                contents = listing.get("Contents", [])
                if len(contents) <= self._max_cached:
                    return

                contents.sort(key=lambda obj: obj.get("LastModified", ""))
                overflow = len(contents) - self._max_cached
                to_delete = contents[:overflow]

                delete_keys = [{"Key": obj["Key"]} for obj in to_delete]
                await s3.delete_objects(
                    Bucket=self._bucket,
                    Delete={"Objects": delete_keys, "Quiet": True},
                )
                logger.info(
                    "[R2Uploader] 清理 %d 张旧图（保留 %d）",
                    len(delete_keys), self._max_cached,
                )

        except Exception as e:
            logger.warning("[R2Uploader] 清理旧图失败: %s", e)

    async def close(self) -> None:
        """兼容接口：aioboto3 每次创建临时 session，无需显式关闭"""
        pass