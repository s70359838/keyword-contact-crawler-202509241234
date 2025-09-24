import os
import sys

# 确保以可执行所在目录为当前工作目录，避免路径问题
try:
    os.chdir(os.path.dirname(sys.executable))
except Exception:
    pass

from app.server import run_server

if __name__ == '__main__':
    run_server()


