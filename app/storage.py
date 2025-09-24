import json
import os
import sqlite3
import time
from typing import Dict

from . import config

os.makedirs(os.path.dirname(config.STATE_DB), exist_ok=True)

SCHEMA = """
CREATE TABLE IF NOT EXISTS contacts (
  id INTEGER PRIMARY KEY,
  keyword TEXT,
  lang TEXT,
  contact_type TEXT,
  contact_value TEXT,
  source_url TEXT,
  page_title TEXT,
  site_domain TEXT,
  first_seen_utc TEXT DEFAULT (datetime('now')),
  UNIQUE(contact_type, contact_value, site_domain)
);
"""


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(config.STATE_DB)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.executescript(SCHEMA)
    return conn


class ResultWriter:
    def __init__(self):
        os.makedirs(os.path.dirname(config.RESULTS_ZH), exist_ok=True)
        os.makedirs(os.path.dirname(config.RESULTS_EN), exist_ok=True)
        self.fp_zh = open(config.RESULTS_ZH, 'a', encoding='utf-8')
        self.fp_en = open(config.RESULTS_EN, 'a', encoding='utf-8')

    def close(self):
        try:
            self.fp_zh.close()
        except Exception:
            pass
        try:
            self.fp_en.close()
        except Exception:
            pass

    def write_record(self, record: Dict):
        line = json.dumps(record, ensure_ascii=False)
        lang = (record.get('lang') or '').lower()
        if lang.startswith('zh'):
            self.fp_zh.write(line + "\n"); self.fp_zh.flush()
        else:
            self.fp_en.write(line + "\n"); self.fp_en.flush()


def save_contact(conn: sqlite3.Connection, rec: Dict) -> bool:
    try:
        conn.execute(
            """
            INSERT INTO contacts(keyword, lang, contact_type, contact_value, source_url, page_title, site_domain)
            VALUES(?,?,?,?,?,?,?)
            """,
            (
                rec.get('keyword'), rec.get('lang'), rec.get('contact_type'), rec.get('contact_value'),
                rec.get('source_url'), rec.get('page_title'), rec.get('site_domain'),
            ),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def export_snapshot() -> str:
    ts = time.strftime('%Y%m%d_%H%M%S')
    os.makedirs(config.EXPORT_DIR, exist_ok=True)
    out_path = os.path.join(config.EXPORT_DIR, f'snapshot_{ts}.txt')
    with open(out_path, 'w', encoding='utf-8') as out:
        for p in (config.RESULTS_ZH, config.RESULTS_EN):
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as fp:
                    for line in fp:
                        out.write(line)
    return out_path
