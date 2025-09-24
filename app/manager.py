import asyncio
from collections import deque
from typing import Deque, Optional

from aiohttp import web
import logging

from .crawler import Crawler
from .searchers import gather_seeds
from .storage import get_conn, save_contact, ResultWriter, export_snapshot


class CrawlManager:
    def __init__(self):
        self.keywords: Deque[str] = deque()
        self.active_keyword: Optional[str] = None
        self.paused: Optional[asyncio.Event] = None
        self.running_task: Optional[asyncio.Task] = None
        self.conn = get_conn()
        self.writer = ResultWriter()
        self.crawler = Crawler()
        self._lock: Optional[asyncio.Lock] = None

    def init_async(self):
        # 在事件循环已建立后创建 asyncio 原语，避免跨循环错误
        self.paused = asyncio.Event()
        self.paused.clear()
        self._lock = asyncio.Lock()

    async def close(self):
        try:
            self.writer.close()
        finally:
            self.conn.close()

    async def add_keyword(self, kw: str):
        async with self._lock:
            self.keywords.append(kw)

    async def switch_keyword(self, kw: str):
        async with self._lock:
            self.keywords.appendleft(kw)
            self.active_keyword = None  # 让调度器立刻切换

    async def pause(self):
        if self.paused:
            self.paused.set()

    async def resume(self):
        if self.paused:
            self.paused.clear()

    async def export(self) -> str:
        return export_snapshot()

    async def _on_record(self, rec: dict):
        inserted = save_contact(self.conn, rec)
        if inserted:
            self.writer.write_record(rec)

    async def scheduler(self):
        while True:
            # 暂停期间不调度
            while self.paused and self.paused.is_set():
                await asyncio.sleep(0.2)
            # 取关键词
            async with self._lock:
                if not self.active_keyword:
                    if self.keywords:
                        self.active_keyword = self.keywords.popleft()
                    else:
                        await asyncio.sleep(0.3)
                        continue
                kw = self.active_keyword
            # 拉取种子并抓取
            try:
                seeds = await gather_seeds(kw)
                await self.crawler.crawl_urls(kw, seeds, self._on_record, paused_event=self.paused)
            except Exception:
                # 简化：忽略单轮异常，继续下一轮
                await asyncio.sleep(0.5)
            # 一轮结束，清空 active
            async with self._lock:
                self.active_keyword = None


async def create_app(mgr: CrawlManager) -> web.Application:
    app = web.Application()
    # 简单文件日志，便于 Windows 双击 exe 排障
    logging.basicConfig(filename=str((web.__file__)).replace('web_app.py','crawler.log'), level=logging.INFO)

    async def handle_root(request):
        raise web.HTTPFound('/ui')

    async def handle_add_keyword(request):
        kw = None
        if request.method == 'POST':
            try:
                data = await request.json()
                kw = (data or {}).get('keyword')
            except Exception:
                kw = None
        if not kw:
            kw = request.query.get('keyword')
        if not kw:
            return web.json_response({'ok': False, 'error': 'keyword required'}, status=400)
        await mgr.add_keyword(kw)
        return web.json_response({'ok': True})

    async def handle_switch_keyword(request):
        kw = None
        if request.method == 'POST':
            try:
                data = await request.json()
                kw = (data or {}).get('keyword')
            except Exception:
                kw = None
        if not kw:
            kw = request.query.get('keyword')
        if not kw:
            return web.json_response({'ok': False, 'error': 'keyword required'}, status=400)
        await mgr.switch_keyword(kw)
        return web.json_response({'ok': True})

    async def handle_pause(request):
        await mgr.pause()
        return web.json_response({'ok': True})

    async def handle_resume(request):
        await mgr.resume()
        return web.json_response({'ok': True})

    async def handle_export(request):
        path = await mgr.export()
        return web.json_response({'ok': True, 'path': path})

    async def handle_status(request):
        return web.json_response({
            'paused': mgr.paused.is_set(),
            'active_keyword': mgr.active_keyword,
            'queue_size': len(mgr.keywords),
        })

    async def handle_ui(request):
        html = """
<!doctype html>
<html lang=zh>
<meta charset=utf-8>
<title>Crawler Control</title>
<style>body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;margin:24px;max-width:800px}input,button{font-size:16px;padding:6px 10px;margin:4px}</style>
<h2>关键词爬虫控制台</h2>
<div>
  <form onsubmit="evt(event,'add')">
    <input id=kw placeholder="输入关键词"> <button>追加关键词</button>
  </form>
  <p>
    <button onclick="call('/pause')">暂停</button>
    <button onclick="call('/resume')">继续</button>
    <button onclick="exportNow()">导出快照</button>
    <button onclick="statusNow()">查看状态</button>
  </p>
  <pre id=out></pre>
</div>
<script>
async function evt(e, t){e.preventDefault(); const kw=document.getElementById('kw').value.trim(); if(!kw) return; const r= await fetch('/add_keyword?keyword='+encodeURIComponent(kw)); document.getElementById('out').textContent= await r.text();}
async function call(path){const r= await fetch(path); document.getElementById('out').textContent= await r.text();}
async function exportNow(){const r= await fetch('/export'); document.getElementById('out').textContent= await r.text();}
async function statusNow(){const r= await fetch('/status'); document.getElementById('out').textContent= await r.text();}
</script>
"""
        return web.Response(text=html, content_type='text/html')

    app.add_routes([
        web.get('/', handle_root),
        web.get('/ui', handle_ui),
        web.get('/add_keyword', handle_add_keyword),
        web.post('/add_keyword', handle_add_keyword),
        web.get('/switch_keyword', handle_switch_keyword),
        web.post('/switch_keyword', handle_switch_keyword),
        web.get('/pause', handle_pause),
        web.post('/pause', handle_pause),
        web.get('/resume', handle_resume),
        web.post('/resume', handle_resume),
        web.get('/export', handle_export),
        web.post('/export', handle_export),
        web.get('/status', handle_status),
    ])

    return app
