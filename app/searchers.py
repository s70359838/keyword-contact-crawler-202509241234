import asyncio
import re
from typing import List

import aiohttp
from bs4 import BeautifulSoup

from . import config
from .utils import pick_user_agent

HEADERS_BASE = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

async def fetch_text(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url, timeout=config.REQUEST_TIMEOUT, headers={"User-Agent": pick_user_agent(), **HEADERS_BASE}) as resp:
        if resp.status != 200:
            return ""
        return await resp.text(errors="ignore")


def extract_links_from_html(html: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("http"):
            links.append(href)
    return links


async def search_duckduckgo(session: aiohttp.ClientSession, keyword: str) -> List[str]:
    urls: List[str] = []
    for page in range(1, 4):  # 前3页
        q = aiohttp.helpers.quote(keyword)
        url = f"https://duckduckgo.com/html/?q={q}&s={(page-1)*30}"
        html = await fetch_text(session, url)
        if not html:
            continue
        for link in extract_links_from_html(html):
            if "duckduckgo.com" in link:
                continue
            urls.append(link)
        if len(urls) >= config.MAX_SEED_RESULTS_PER_ENGINE:
            break
    return urls[: config.MAX_SEED_RESULTS_PER_ENGINE]


async def search_mojeek(session: aiohttp.ClientSession, keyword: str) -> List[str]:
    urls: List[str] = []
    for page in range(1, 4):
        q = aiohttp.helpers.quote(keyword)
        url = f"https://www.mojeek.com/search?q={q}&s={(page-1)*10}"
        html = await fetch_text(session, url)
        if not html:
            continue
        for link in extract_links_from_html(html):
            if "mojeek.com" in link:
                continue
            urls.append(link)
        if len(urls) >= config.MAX_SEED_RESULTS_PER_ENGINE:
            break
    return urls[: config.MAX_SEED_RESULTS_PER_ENGINE]


async def gather_seeds(keyword: str) -> List[str]:
    async with aiohttp.ClientSession() as session:
        res = await asyncio.gather(
            search_duckduckgo(session, keyword),
            search_mojeek(session, keyword),
            return_exceptions=True,
        )
    seeds: List[str] = []
    for r in res:
        if isinstance(r, list):
            seeds.extend(r)
    # 去重
    seen = set()
    uniq = []
    for u in seeds:
        if u not in seen:
            uniq.append(u)
            seen.add(u)
    return uniq
