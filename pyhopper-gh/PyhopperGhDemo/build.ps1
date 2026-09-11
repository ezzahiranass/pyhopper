param(
    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Debug"
)

$ErrorActionPreference = "Stop"
$project = Join-Path $PSScriptRoot "PyhopperGhDemo.csproj"

if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
    throw "dotnet was not found. Install the .NET 8 SDK, then rerun this script."
}

$sdkList = & dotnet --list-sdks
if (-not $sdkList) {
    throw "No .NET SDK is installed. Install the .NET 8 SDK, then rerun this script."
}

& dotnet build $project --configuration $Configuration
if ($LASTEXITCODE -ne 0) {
    throw "Build failed."
}

$output = Join-Path $PSScriptRoot "bin\$Configuration\net48\PyhopperGhDemo.gha"
Write-Host "Built: $output"
