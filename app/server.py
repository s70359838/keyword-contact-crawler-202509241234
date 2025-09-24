import asyncio
from aiohttp import web
import webbrowser
import socket
import os
import logging
import platform
try:
    import ctypes
except Exception:
    ctypes = None

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


def _message_box(title: str, text: str):
    if platform.system().lower().startswith('win') and ctypes:
        try:
            ctypes.windll.user32.MessageBoxW(0, text, title, 0x10)
            return
        except Exception:
            pass
    print(f"{title}: {text}")


def run_server():
    # 提前配置日志，避免异常丢失
    try:
        os.makedirs(config.DATA_DIR, exist_ok=True)
        logging.basicConfig(filename=os.path.join(config.DATA_DIR, 'server_boot.log'), level=logging.INFO)
    except Exception:
        logging.basicConfig(level=logging.INFO)

    async def main():
        mgr = CrawlManager()
        app = await create_app(mgr)
        app['mgr'] = mgr
        app.on_startup.append(_on_startup)
        app.on_cleanup.append(_on_cleanup)

        host = config.CONTROL_HOST
        desired_port = int(os.environ.get('CRAWLER_PORT', str(config.CONTROL_PORT)))
        # 若指定端口不可用，使用0让系统分配
        try_specific = True
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, desired_port))
        except Exception:
            try_specific = False

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, desired_port if try_specific else 0)
        await site.start()
        actual_port = desired_port
        try:
            # 读取实际绑定端口
            for s in site._server.sockets:
                actual_port = s.getsockname()[1]
                break
        except Exception:
            pass

        url = f"http://{host}:{actual_port}/" if host != '0.0.0.0' else f"http://127.0.0.1:{actual_port}/"
        if not os.environ.get('CRAWLER_NO_BROWSER'):
            try:
                webbrowser.open(url)
            except Exception:
                pass
        await asyncio.Event().wait()

    try:
        asyncio.run(main())
    except Exception as e:
        logging.exception("Fatal error during server startup")
        _message_box("Crawler 启动失败", f"错误: {e}\n日志: {os.path.join(config.DATA_DIR, 'server_boot.log')}")


if __name__ == '__main__':
    run_server()
