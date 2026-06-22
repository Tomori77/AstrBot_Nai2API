"""
NSFW 判定器

通过「提示词关键词命中」+「用户显式 --nsfw 标记」双触发判定。
任一命中即视为 NSFW。
"""

import re

from astrbot.api import logger


# 内置 NSFW 关键词表（中英混合，覆盖常见 NSFW 标签）
BUILTIN_NSFW_KEYWORDS = [
    # 通用标记
    "nsfw", "nude", "nudity", "nudes", "completely nude", "explicit",
    "porn", "pornographic", "xxx", "18+", "uncensored",
    # 裸露
    "naked", "topless", "bottomless", "bare skin", "revealing",
    "nipples", "areolae", "breast", "oppai", "chest",
    # 性器
    "penis", "dick", "cock", "vagina", "pussy", "anus", "anal",
    "testicles", "balls", "clitoris", "clit", "cameltoe",
    # 性行为
    "sex", "sexual", "intercourse", "penetration", "double penetration",
    "cum", "creampie", "ejaculation", "cum in mouth", "cum on face",
    "bukkake", "swallowing", "masturbation", "orgasm", "pussy juice",
    "blowjob", "fellatio", "handjob", "paizuri", "titfuck",
    "cunnilingus", "deepthroat", "rimjob", "fingering", "fisting",
    "gangbang", "threesome", "group sex", "orgy",
    "missionary", "doggystyle", "cowgirl", "riding", "spread legs", "spread pussy",
    # 性玩具 / 束缚
    "dildo", "vibrator", "sex toy", "bondage", "bdsm", "restrained",
    # 其他常见 NSFW 标签
    "hentai", "ecchi", "smut", "lewd",
    "futanari", "futa", "dickgirl", "tentacle", "tentacles",
    "rape", "lactation", "pregnant", "peeing", "urination",
    "ahegao", "mind control",
    # 中文
    "裸体", "裸照", "全裸", "露点", "裸露", "色情", "成人", "性器", "性交",
    "阴茎", "肉棒", "阴道", "小穴", "屁股", "胸部", "内裤", "性玩具",
    "做爱", "自慰", "高潮", "潮吹", "内射", "口交", "乳交", "肛交", "群交",
    "颜射", "骑乘", "后入", "传教士", "开腿",
    "强奸", "乱伦", "触手", "扶他", "束缚",
    "本子", "里番", "工口", "H场景",
]


def _normalize_keywords(custom_keywords: str) -> list[str]:
    """把自定义关键词字符串解析为小写列表"""
    if not custom_keywords:
        return []
    return [k.strip().lower() for k in custom_keywords.split(",") if k.strip()]


def _normalize_prompt(prompt: str) -> str:
    """提示词归一化：小写 + 去多余空格，便于匹配"""
    return re.sub(r"\s+", " ", prompt.strip().lower())


class NsfwChecker:
    """NSFW 判定器"""

    def __init__(self, custom_keywords: str = ""):
        self._custom = _normalize_keywords(custom_keywords)
        if self._custom:
            logger.info("[NsfwChecker] 已加载 %d 个自定义 NSFW 关键词（与内置合并）", len(self._custom))

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

        normalized = _normalize_prompt(prompt)
        if not normalized:
            return False

        # 内置关键词 + 用户自定义关键词合并去重
        keywords = list(dict.fromkeys([*BUILTIN_NSFW_KEYWORDS, *self._custom]))
        for kw in keywords:
            if kw and kw in normalized:
                return True
        return False