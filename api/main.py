from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from api.routers.device import router as device_router
from api.routers.status import router as status_router

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parents[1]

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return FileResponse(BASE_DIR / "templates" / "index.html")

app.include_router(device_router)
app.include_router(status_router)