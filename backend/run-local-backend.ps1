$ErrorActionPreference = "Stop"

$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
$env:PYTHONPATH = Join-Path $PSScriptRoot ".python-deps"
Set-Location $PSScriptRoot

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$codexPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if (Test-Path $venvPython) {
  & $venvPython manage.py runserver 127.0.0.1:8000
} elseif (Test-Path $codexPython) {
  & $codexPython manage.py runserver 127.0.0.1:8000
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  python manage.py runserver 127.0.0.1:8000
} else {
  py -3 manage.py runserver 127.0.0.1:8000
}
