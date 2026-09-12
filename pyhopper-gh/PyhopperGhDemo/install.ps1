param(
    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Debug"
)

$ErrorActionPreference = "Stop"
$source = Join-Path $PSScriptRoot "bin\$Configuration\net48\PyhopperGhDemo.gha"
$targetDirectory = Join-Path $env:APPDATA "Grasshopper\Libraries\PyhopperGhDemo"
$target = Join-Path $targetDirectory "PyhopperGhDemo.gha"

if (-not (Test-Path -LiteralPath $source)) {
    throw "Build output not found at '$source'. Run .\build.ps1 first."
}

New-Item -ItemType Directory -Force -Path $targetDirectory | Out-Null
Copy-Item -LiteralPath $source -Destination $target -Force
Unblock-File -LiteralPath $target

Write-Host "Installed: $target"
Write-Host "Restart Rhino and Grasshopper to load the plugin."
