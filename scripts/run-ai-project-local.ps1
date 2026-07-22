param(
    [string]$PythonPath = "C:\Python310\python.exe",
    [int]$Port = 8000
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendPath = Join-Path $projectRoot "backend"
$databasePath = Join-Path $backendPath "db.ai-project-test.sqlite3"

if (-not (Test-Path -LiteralPath $PythonPath)) {
    $PythonPath = "python"
}

if (-not (Test-Path -LiteralPath $databasePath)) {
    Write-Error "AI test database is missing. Run scripts\prepare-ai-project-test.ps1 first."
    exit 1
}

$env:CSAA_DB_PATH = $databasePath
Set-Location $backendPath
& $PythonPath manage.py runserver "127.0.0.1:$Port" --noreload
