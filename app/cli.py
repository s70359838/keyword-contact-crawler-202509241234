import argparse
import asyncio
import os

from . import config
from .searchers import gather_seeds
from .crawler import Crawler
from .storage import get_conn, save_contact, ResultWriter, export_snapshot


def run_start(keyword: str, demo: bool = False):
    async def main():
        seeds = await gather_seeds(keyword)
        if demo:
            seeds = seeds[: min(len(seeds), 10)]
        crawler = Crawler()
        conn = get_conn()
        writer = ResultWriter()

        async def on_record(rec: dict):
            inserted = save_contact(conn, rec)
            if inserted:
                writer.write_record(rec)

        try:
            await crawler.crawl_urls(keyword, seeds, on_record)
        finally:
            writer.close()
            conn.close()

    asyncio.run(main())


def run_export_now():
    path = export_snapshot()
    print(f"snapshot exported: {path}")


def main():
    parser = argparse.ArgumentParser(description='Keyword contact crawler')
    sub = parser.add_subparsers(dest='cmd')

    p_start = sub.add_parser('start')
    p_start.add_argument('--keyword', required=True)
    p_start.add_argument('--demo', action='store_true')

    sub.add_parser('export-now')
    sub.add_parser('serve')

    p_add = sub.add_parser('add-keyword')
    p_add.add_argument('--keyword', required=True)

    p_switch = sub.add_parser('switch-keyword')
    p_switch.add_argument('--keyword', required=True)

    sub.add_parser('pause')
    sub.add_parser('resume')

    args = parser.parse_args()
    if args.cmd == 'start':
        run_start(args.keyword, demo=args.demo)
    elif args.cmd == 'export-now':
        run_export_now()
    elif args.cmd == 'serve':
        from .server import run_server
        run_server()
    elif args.cmd == 'add-keyword':
        import requests
        from . import config
        r = requests.post(f"http://{config.CONTROL_HOST}:{config.CONTROL_PORT}/add_keyword", json={'keyword': args.keyword})
        print(r.text)
    elif args.cmd == 'switch-keyword':
        import requests
        from . import config
        r = requests.post(f"http://{config.CONTROL_HOST}:{config.CONTROL_PORT}/switch_keyword", json={'keyword': args.keyword})
        print(r.text)
    elif args.cmd == 'pause':
        import requests
        from . import config
        r = requests.post(f"http://{config.CONTROL_HOST}:{config.CONTROL_PORT}/pause")
        print(r.text)
    elif args.cmd == 'resume':
        import requests
        from . import config
        r = requests.post(f"http://{config.CONTROL_HOST}:{config.CONTROL_PORT}/resume")
        print(r.text)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
