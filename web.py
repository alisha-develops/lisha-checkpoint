from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent

@router.get("/", response_class=HTMLResponse)
async def home():
    html_path = BASE_DIR / "landing.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"), status_code=200)
    return HTMLResponse(content="<h1>lisha-checkpoint is active!</h1>", status_code=200)