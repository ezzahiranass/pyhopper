param(
    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Debug"
)

& (Join-Path $PSScriptRoot "build.ps1") -Configuration $Configuration
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

& (Join-Path $PSScriptRoot "install.ps1") -Configuration $Configuration
