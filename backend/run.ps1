# 在任意目录运行此脚本；依赖与配置均来自脚本所在的 backend 目录。
$ErrorActionPreference = 'Stop'
$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Missing .venv. Run: python -m venv .venv; .\.venv\Scripts\python.exe -X utf8 -m pip install -r requirements.txt'
}
Push-Location $PSScriptRoot
try {
    & $pythonPath -X utf8 -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload --reload-include '.env'
    if ($LASTEXITCODE -ne 0) { throw 'Backend exited with an error. See the output above.' }
} finally {
    Pop-Location
}
