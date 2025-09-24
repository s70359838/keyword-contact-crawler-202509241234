import asyncio
import random
import re
from typing import Optional

from . import config


def pick_user_agent() -> str:
    return random.choice(config.DEFAULT_USER_AGENTS)


def is_probably_chinese(text: str) -> bool:
    # 粗略中文判断：包含中文字符或常见中文词
    if re.search(r"[\u4e00-\u9fff]", text or ""):
        return True
    for w in config.LANG_ZH_HINTS:
        if w.lower() in (text or "").lower():
            return True
    return False


class RateLimiter:
    def __init__(self, rate_per_sec: float):
        self._interval = 1.0 / max(rate_per_sec, 0.001)
        self._last = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = asyncio.get_event_loop().time()
            delta = now - self._last
            if delta < self._interval:
                await asyncio.sleep(self._interval - delta)
            self._last = asyncio.get_event_loop().time()


def clean_text(s: Optional[str]) -> str:
    return (s or "").strip().replace("\r", " ").replace("\n", " ")
