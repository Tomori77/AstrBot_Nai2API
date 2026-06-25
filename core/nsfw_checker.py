"""
NSFW 判定器

通过「提示词关键词命中」+「用户显式 --nsfw 标记」双触发判定。
关键词完全来自配置项 nsfw_keywords，无内置词表。
"""

import re

from astrbot.api import logger


def _normalize_keywords(custom_keywords: str) -> list[str]:
    """把逗号分隔的关键词字符串解析为小写列表，去空格去空"""
    if not custom_keywords:
        return []
    return [k.strip().lower() for k in custom_keywords.split(",") if k.strip()]


def _normalize_prompt(prompt: str) -> str:
    """提示词归一化：小写 + 去多余空格，便于匹配"""
    return re.sub(r"\s+", " ", prompt.strip().lower())


class NsfwChecker:
    """NSFW 判定器，关键词完全来自配置"""

    def __init__(self, keywords: str = ""):
        self._keywords = _normalize_keywords(keywords)
        if self._keywords:
            logger.info("[NsfwChecker] 已加载 %d 个 NSFW 关键词", len(self._keywords))
        else:
            logger.info("[NsfwChecker] 未配置 NSFW 关键词，仅 --nsfw 显式标记生效")

    def check(self, prompt: str, explicit_flag: bool = False) -> bool:
        """
        判定是否 NSFW。

        Args:
            prompt: 提示词原文
            explicit_flag: 用户是否显式加了 --nsfw 标记

        Returns:
            True 表示 NSFW，False 表示安全
        """
        if explicit_flag:
            return True

        if not self._keywords:
            return False

        normalized = _normalize_prompt(prompt)
        if not normalized:
            return False

        for kw in self._keywords:
            if kw and kw in normalized:
                return True
        return False