"""
Web interface and static file serving for Git-Github MCP.
"""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

router = APIRouter()

# Directory configuration
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
dist_dir = project_root / "web" / "dist"


def setup_webapp(app):
    """
    Mounts the static files and sets up the SPA routing.
    """
    if dist_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(dist_dir / "assets")), name="assets")

        @app.get("/{full_path:path}", response_class=HTMLResponse)
        async def serve_spa(request: Request, full_path: str):
            # Skip API paths
            if full_path.startswith("api/") or full_path.startswith("mcp"):
                return None

            index_path = dist_dir / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            return HTMLResponse(
                content=("<h1>Frontend not built</h1><p>Run <code>npm run build</code> in web folder</p>"),
                status_code=404,
            )
    else:

        @app.get("/", response_class=HTMLResponse)
        async def dev_hint():
            return HTMLResponse(
                content=("<h1>Static files missing</h1><p>Expected <code>web/dist</code> but it does not exist.</p>")
            )
