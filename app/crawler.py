import asyncio
import json
import re
import urllib.parse
from typing import Dict, List, Optional, Set, Tuple

import aiohttp
from bs4 import BeautifulSoup
import tldextract
import urllib.robotparser as robotparser

from . import config
from .utils import RateLimiter, pick_user_agent, clean_text
from .extractors import extract_all

HEADERS_BASE = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

class RobotsCache:
    def __init__(self):
        self.cache: Dict[str, Tuple[float, robotparser.RobotFileParser]] = {}
        self.lock = asyncio.Lock()

    async def can_fetch(self, session: aiohttp.ClientSession, url: str, ua: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        async with self.lock:
            rp_tuple = self.cache.get(base)
            now = asyncio.get_event_loop().time()
            if not rp_tuple or now - rp_tuple[0] > config.ROBOTS_CACHE_TTL:
                robots_url = urllib.parse.urljoin(base, "/robots.txt")
                rp = robotparser.RobotFileParser()
                try:
                    async with session.get(robots_url, headers={"User-Agent": ua, **HEADERS_BASE}, timeout=config.CONNECT_TIMEOUT) as resp:
                        if resp.status == 200:
                            txt = await resp.text(errors="ignore")
                            rp.parse(txt.splitlines())
                        else:
                            rp.parse("")
                except Exception:
                    rp.parse("")
                self.cache[base] = (now, rp)
                rp_tuple = self.cache[base]
        rp = rp_tuple[1]
        try:
            return rp.can_fetch(ua, url)
        except Exception:
            return True


class DomainLimiter:
    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}

    def get(self, host: str) -> RateLimiter:
        if host not in self.limiters:
            self.limiters[host] = RateLimiter(config.PER_HOST_RATE_LIMIT)
        return self.limiters[host]


class Crawler:
    def __init__(self):
        self.robots = RobotsCache()
        self.domain_limiter = DomainLimiter()

    async def fetch(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        ua = pick_user_agent()
        if not await self.robots.can_fetch(session, url, ua):
            return None
        parsed = urllib.parse.urlparse(url)
        await self.domain_limiter.get(parsed.netloc).acquire()
        try:
            async with session.get(url, headers={"User-Agent": ua, **HEADERS_BASE}, timeout=config.REQUEST_TIMEOUT) as resp:
                if resp.status != 200:
                    return None
                ctype = resp.headers.get('Content-Type', '')
                if 'text/html' not in ctype and 'application/xhtml+xml' not in ctype:
                    return None
                return await resp.text(errors="ignore")
        except Exception:
            return None

    def extract_domain(self, url: str) -> str:
        t = tldextract.extract(url)
        return ".".join([p for p in [t.domain, t.suffix] if p])

    def parse_contacts(self, html: str) -> Tuple[str, List[Tuple[str, str]]]:
        soup = BeautifulSoup(html, "html.parser")
        title = clean_text(soup.title.text if soup.title else "")
        texts = [title]
        for tag in soup.find_all(text=True):
            text = str(tag)
            if text and not re.match(r"^\s+$", text):
                texts.append(text)
        content = "\n".join(texts)
        pairs = extract_all(content)
        return title, pairs

    async def crawl_urls(self, keyword: str, urls: List[str], on_record, paused_event: Optional[asyncio.Event] = None):
        sem = asyncio.Semaphore(config.GLOBAL_CONCURRENCY)
        async with aiohttp.ClientSession() as session:
            async def worker(url: str):
                async with sem:
                    if paused_event and paused_event.is_set():
                        return
                    html = await self.fetch(session, url)
                    if not html:
                        return
                    title, pairs = self.parse_contacts(html)
                    if not pairs:
                        return
                    domain = self.extract_domain(url)
                    lang = 'zh' if re.search(r"[\u4e00-\u9fff]", html) else 'en'
                    for ctype, cval in pairs:
                        if paused_event and paused_event.is_set():
                            return
                        rec = {
                            'keyword': keyword,
                            'lang': lang,
                            'contact_type': ctype,
                            'contact_value': cval,
                            'source_url': url,
                            'page_title': title,
                            'site_domain': domain,
                        }
                        await on_record(rec)
            await asyncio.gather(*[worker(u) for u in urls])
