# Repo-wide check: unit tests -> API tests -> strict docs build -> optional Rhino 8 oracle suite.
# Usage: .\scripts\check.ps1        (set $env:RHINO_ORACLE = "1" to include the oracle suite)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"

Write-Host "== unit tests (tests/)"
& $py -m unittest discover -s (Join-Path $root "tests") -t $root -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "== API tests (pyhopper-web/api/test_*.py)"
& $py -m unittest discover -s (Join-Path $root "pyhopper-web\api") -p "test_*.py" -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "== docs (mkdocs build --strict)"
$env:DISABLE_MKDOCS_2_WARNING = "true"
& $py -m mkdocs build --strict -f (Join-Path $root "mkdocs.yml")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($env:RHINO_ORACLE -eq "1") {
    Write-Host "== Rhino 8 oracle suite (rhino-test/oracle)"
    $rpy = Join-Path $root "rhino-test\.venv\Scripts\python.exe"
    & $rpy -m unittest discover -s (Join-Path $root "rhino-test\oracle") -t (Join-Path $root "rhino-test") -v
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
Write-Host "== all checks passed"
