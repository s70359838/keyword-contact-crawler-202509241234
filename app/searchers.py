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


async def resolve_redirects(session: aiohttp.ClientSession, url: str) -> str:
    try:
        async with session.get(url, allow_redirects=True, timeout=10, headers={"User-Agent": pick_user_agent(), **HEADERS_BASE}) as resp:
            return str(resp.url)
    except Exception:
        return url


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


async def search_baidu(session: aiohttp.ClientSession, keyword: str) -> List[str]:
    urls: List[str] = []
    for page in range(0, 3):  # pn=0,10,20
        q = aiohttp.helpers.quote(keyword)
        url = f"https://www.baidu.com/s?wd={q}&pn={page*10}"
        html = await fetch_text(session, url)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        raw = []
        for h3 in soup.select('h3 a[href]'):
            href = h3.get('href')
            if href and href.startswith('http'):
                raw.append(href)
        # 解析跳转，拿到真实目标链接，避免命中 baidu.com/link 的 robots 限制
        if raw:
            resolved = await asyncio.gather(*[resolve_redirects(session, u) for u in raw], return_exceptions=True)
            for r in resolved:
                if isinstance(r, str) and r.startswith('http') and 'baidu.com' not in r:
                    urls.append(r)
        if len(urls) >= config.MAX_SEED_RESULTS_PER_ENGINE:
            break
    return urls[: config.MAX_SEED_RESULTS_PER_ENGINE]


async def search_sogou(session: aiohttp.ClientSession, keyword: str) -> List[str]:
    urls: List[str] = []
    for page in range(1, 4):
        q = aiohttp.helpers.quote(keyword)
        url = f"https://www.sogou.com/web?query={q}&page={page}"
        html = await fetch_text(session, url)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        raw = []
        for a in soup.select('a[href]'):
            href = a.get('href')
            if href and href.startswith('http'):
                raw.append(href)
        if raw:
            resolved = await asyncio.gather(*[resolve_redirects(session, u) for u in raw], return_exceptions=True)
            for r in resolved:
                if isinstance(r, str) and r.startswith('http') and 'sogou.com' not in r:
                    urls.append(r)
        if len(urls) >= config.MAX_SEED_RESULTS_PER_ENGINE:
            break
    return urls[: config.MAX_SEED_RESULTS_PER_ENGINE]


async def gather_seeds(keyword: str) -> List[str]:
    async with aiohttp.ClientSession() as session:
        res = await asyncio.gather(
            search_duckduckgo(session, keyword),
            search_mojeek(session, keyword),
            # 额外增加国内常用搜索源：百度与搜狗（HTML 结果页）
            search_baidu(session, keyword),
            search_sogou(session, keyword),
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
