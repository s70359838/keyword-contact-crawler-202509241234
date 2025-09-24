# 关键词爬取与联系方式采集器

支持中文/英文关键词，免费多源发现 + 有界爬取，抽取邮箱/电话/微信/QQ/Telegram/WhatsApp/社媒链接等；中英分开保存至 TXT（JSON Lines），SQLite 去重，支持随时暂停/继续/导出与关键词管理；可打包为 Windows EXE。

## 运行

- 一次性小规模演示（前10个种子）
  - macOS/Linux: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && python -m app.cli start --keyword "安卓逆向" --demo`
  - Windows(PowerShell): `py -m venv .venv; .\.venv\\Scripts\\Activate.ps1; pip install -r requirements.txt; python -m app.cli start --keyword "安卓逆向" --demo`

- 启动控制服务（支持开始/暂停/继续/切换关键词/导出）
  - `python -m app.cli serve`
  - 新开终端：
    - 添加关键词：`python -m app.cli add-keyword --keyword "安卓逆向"`
    - 追加英文：`python -m app.cli add-keyword --keyword "Android reverse engineering"`
    - 暂停：`python -m app.cli pause` ；继续：`python -m app.cli resume`
    - 导出快照：`python -m app.cli export-now`
  - 浏览器控制台：`http://127.0.0.1:8848/ui`

## 输出文件
- 中文：`data/results_zh.txt`
- 英文：`data/results_en.txt`
- 状态库：`data/state.sqlite`（用于去重与断点续跑）
- 快照：`export/snapshot_YYYYMMDD_HHMMSS.txt`

## 合规
仅抓取公开网页；遵守 robots.txt 与站点 ToS；不登录、不绕过验证码/风控、不抓取私域内容。

---
## Windows 打包与下载

### 本地打包（Windows）
1) PowerShell 执行：
```
py -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
```
2) 产物：`dist\crawler.exe`（双击运行即启动服务，浏览器开 `http://127.0.0.1:8848/ui` 控制）

### GitHub Actions 自动打包
- 推送到 `main/master` 或手动触发 `Build Windows EXE` 工作流
- 下载产物：Artifacts 中的 `crawler-windows`（含 `crawler.exe`）

## 会话累计总结
- 主要目的：Windows 可用、可随时暂停导出/继续的关键词爬虫，按中英文分开统计，免费优先且去重。
- 完成任务：
  - 初始化工程与依赖；多源种子搜索（DuckDuckGo/Mojeek）；异步爬虫（robots/按域限速）；联系方式抽取；SQLite 去重与 JSONL 双文件落盘；CLI（start/export-now/serve/add-keyword/switch-keyword/pause/resume）。
  - 演示运行：已产出 `data/results_zh.txt` 与 `data/results_en.txt`，并成功导出快照。
- 关键决策：JSON Lines 文本输出；去重键为 `(contact_type, contact_value, site_domain)`；默认高强度并发；严格遵守 robots；控制面基于本地 HTTP。
- 技术栈：Python 3、aiohttp、BeautifulSoup4、tldextract、phonenumberslite、sqlite3、argparse。
- 涉及文件：`app/*.py`、`requirements.txt`、`README.md`、`data/*`、`export/*`。
