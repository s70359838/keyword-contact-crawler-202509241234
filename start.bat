@echo off
setlocal
REM 数据与导出目录改到用户 LocalAppData，避免无写权限闪退
set CRAWLER_DATA_DIR=%LOCALAPPDATA%\KeywordContactCrawler\data
set CRAWLER_EXPORT_DIR=%LOCALAPPDATA%\KeywordContactCrawler\export
set CRAWLER_PORT=8848
REM 如需禁止自动开浏览器，取消下一行的 REM
REM set CRAWLER_NO_BROWSER=1
start "crawler" /B crawler.exe
exit /b
