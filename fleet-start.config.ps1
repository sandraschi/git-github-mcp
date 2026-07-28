# Per-repo fleet start config for git-github-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'git-github-mcp'
    BackendPort  = 10702
    FrontendPort = 10703
    HealthPath   = '/health'
    WebRoot      = 'D:\Dev\repos\git-github-mcp\web'
    Backend = @{
        Kind          = 'uvicorn-web-app'
        UvicornTarget = 'git_github_mcp.server:web_app'
        SyncExtras    = @('dev')
        Env           = @{ WEB_PORT = '10702' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
