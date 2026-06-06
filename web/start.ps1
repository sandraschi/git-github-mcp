param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoBrowser
)

$RepoRoot = Split-Path -Parent $PSScriptRoot
& (Join-Path $RepoRoot "start.ps1") @PSBoundParameters
