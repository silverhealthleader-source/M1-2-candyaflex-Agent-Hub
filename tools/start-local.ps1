$ErrorActionPreference = 'Stop'
$projectDirectory = Split-Path -Parent $PSScriptRoot
$env:FIREBASE_PROJECT_ID = 'demo-candy-a-academy'
$env:FIRESTORE_EMULATOR_HOST = '127.0.0.1:8088'
$env:APP_ENV = 'development'
$env:PYTHONIOENCODING = 'utf-8'
Set-Location -LiteralPath (Join-Path $projectDirectory 'backend')
& (Join-Path $projectDirectory '.venv/Scripts/python.exe') -m uvicorn app.main:app --host 127.0.0.1 --port 8010
