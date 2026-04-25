from pathlib import Path

from fastapi.responses import HTMLResponse


def get_ui() -> HTMLResponse:
    frontend_path = Path(__file__).resolve().parents[2] / "frontend" / "index.html"
    if frontend_path.exists():
        return HTMLResponse(frontend_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>OpenEnv Code Review Dashboard</h1><p>frontend/index.html not found.</p>")
