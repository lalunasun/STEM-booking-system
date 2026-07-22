param(
    [string]$PythonPath = "C:\Python310\python.exe"
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendPath = Join-Path $projectRoot "backend"
$databasePath = Join-Path $backendPath "db.ai-project-test.sqlite3"
$outputPath = Join-Path $projectRoot "outputs\ai_project\ai_student_learning_profile_10.json"

if (-not (Test-Path -LiteralPath $PythonPath)) {
    $PythonPath = "python"
}

$env:CSAA_DB_PATH = $databasePath
Push-Location $backendPath
try {
    & $PythonPath manage.py migrate --noinput
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    & $PythonPath manage.py seed_ai_project_test
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    & $PythonPath manage.py export_ai_project_json --output $outputPath
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}

Write-Host "AI test database: $databasePath"
Write-Host "AI JSON export: $outputPath"
