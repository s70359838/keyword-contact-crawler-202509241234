param(
  [string]$PyInstallerPath = "",
  [string]$PyExe = "python"
)

# 进入项目根目录
Set-Location -LiteralPath $PSScriptRoot

# 确保虚拟环境存在
if (-Not (Test-Path .venv)) {
  & $PyExe -m venv .venv
}
. .\.venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt pyinstaller

# 生成单文件 EXE（带控制服务与 CLI）
pyinstaller --onefile -n crawler.exe -p app app\server.py

Write-Host "\n构建完成：dist\\crawler.exe"
Write-Host "请将 dist\\crawler.exe 与 data/ export/ 同目录放置（首次运行会自动创建）"
