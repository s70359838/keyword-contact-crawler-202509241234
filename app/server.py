import asyncio
from aiohttp import web
import webbrowser
import socket

from . import config
from .manager import CrawlManager, create_app


async def _on_startup(app: web.Application):
    mgr: CrawlManager = app['mgr']
    # 在应用事件循环中初始化异步原语，避免跨循环问题
    mgr.init_async()
    app['sched_task'] = asyncio.create_task(mgr.scheduler())


async def _on_cleanup(app: web.Application):
    task = app.get('sched_task')
    if task:
        task.cancel()
        try:
            await task
        except Exception:
            pass
    mgr: CrawlManager = app['mgr']
    await mgr.close()


def run_server():
    mgr = CrawlManager()
    app = asyncio.get_event_loop().run_until_complete(create_app(mgr))
    app['mgr'] = mgr
    app.on_startup.append(_on_startup)
    app.on_cleanup.append(_on_cleanup)
    # 打开默认浏览器
    try:
        webbrowser.open(f"http://{config.CONTROL_HOST}:{config.CONTROL_PORT}/")
    except Exception:
        pass
    host = config.CONTROL_HOST
    port = config.CONTROL_PORT
    # 端口占用自动回退
    for p in [port, port + 1, port + 2, port + 10]:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((host, p))
            port = p
            break
        except Exception:
            continue
    try:
        webbrowser.open(f"http://{host}:{port}/")
    except Exception:
        pass
    web.run_app(app, host=host, port=port)


if __name__ == '__main__':
    run_server()
