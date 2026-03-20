# MCPB pack script. Copies source into mcpb/, then packs to dist/.
# Run from repo root.
$ErrorActionPreference = "Stop"
$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
$mcpbDir = $repoRoot + "\mcpb"
$distDir = $repoRoot + "\dist"

# Copy source and build artifacts into mcpb (clean copy)
Remove-Item -Path "$mcpbDir\src" -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item -Path "$repoRoot\src" -Destination "$mcpbDir\src" -Recurse -Force
Copy-Item -Path "$repoRoot\pyproject.toml" -Destination "$mcpbDir\pyproject.toml" -Force
Copy-Item -Path "$repoRoot\requirements.txt" -Destination "$mcpbDir\requirements.txt" -Force
Copy-Item -Path "$repoRoot\README.md" -Destination "$mcpbDir\README.md" -Force

# Exclude dev artifacts from copied src
Remove-Item -Path "$mcpbDir\src\**\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue

# Create dist
New-Item -ItemType Directory -Force -Path $distDir | Out-Null

# Pack
Set-Location $mcpbDir
mcpb pack . "$distDir\git-github-mcp.mcpb"
Set-Location $repoRoot

Write-Host "Built: dist\git-github-mcp.mcpb"
