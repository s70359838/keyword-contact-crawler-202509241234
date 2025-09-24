import os
import sys
import platform
from pathlib import Path

# 基础配置
DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

REQUEST_TIMEOUT = 15
CONNECT_TIMEOUT = 10
PER_HOST_RATE_LIMIT = 1.0  # 每域每秒最多请求数
GLOBAL_CONCURRENCY = 10     # 默认高强度
MAX_SEED_RESULTS_PER_ENGINE = 30  # 每个搜索源抓取前N条链接
MAX_PAGES_PER_DOMAIN = 50
MAX_CRAWL_DEPTH = 2

# 基准目录：普通模式使用项目根目录；打包后使用可执行文件所在目录
if getattr(sys, 'frozen', False):
    if platform.system().lower().startswith('win'):
        # Windows 安装后将数据写入用户目录，避免 Program Files 无写权限导致闪退
        user_base = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData' / 'Local')))
        BASE_DIR = user_base / 'KeywordContactCrawler'
    else:
        BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parents[1]

# 允许环境变量覆盖数据目录
DATA_DIR = str(Path(os.environ.get('CRAWLER_DATA_DIR', str(BASE_DIR / 'data'))))
EXPORT_DIR = str(Path(os.environ.get('CRAWLER_EXPORT_DIR', str(BASE_DIR / 'export'))))

RESULTS_ZH = str(Path(DATA_DIR) / "results_zh.txt")
RESULTS_EN = str(Path(DATA_DIR) / "results_en.txt")
ERROR_LOG = str(Path(DATA_DIR) / "crawler_errors.txt")
STATE_DB = str(Path(DATA_DIR) / "state.sqlite")

ROBOTS_CACHE_TTL = 60 * 60  # 1小时

# 停止关键词扩展的正则提示词
CONTACT_HINT_KEYWORDS = [
    "contact", "联系", "关于", "邮箱", "合作", "商务", "contact-us", "about", "email"
]

# 语言阈值（简单策略）
LANG_ZH_HINTS = ["微信", "联系", "合作", "邮箱", "qq", "企业", "公众号", "知乎", "微博"]

# 控制服务（可由环境变量覆盖）
CONTROL_HOST = os.environ.get("CRAWLER_HOST", "127.0.0.1")
try:
    CONTROL_PORT = int(os.environ.get("CRAWLER_PORT", "8848"))
except Exception:
    CONTROL_PORT = 8848

# 自动循环采集（未暂停时连续采集），间隔可用环境变量覆盖
AUTO_LOOP = os.environ.get("CRAWLER_AUTO_LOOP", "1") not in ("0", "false", "False")
try:
    AUTO_LOOP_INTERVAL_SEC = int(os.environ.get("CRAWLER_LOOP_INTERVAL", "60"))
except Exception:
    AUTO_LOOP_INTERVAL_SEC = 60
