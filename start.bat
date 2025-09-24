@echo off
setlocal
set CRAWLER_PORT=8848
REM 若不想自动打开浏览器，去掉下一行前的 REM
REM set CRAWLER_NO_BROWSER=1
start "crawler" /B crawler.exe
exit /b
