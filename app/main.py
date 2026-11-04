from pathlib import Path

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from app.routers import container_logs, containers, images, networks, stats, ui, volumes

app = FastAPI(title="Lightweight Docker Dashboard", version="1.0")

# Mount Static & Templates
# app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Register Routers
app.include_router(containers.router)
app.include_router(images.router)
app.include_router(networks.router)
app.include_router(volumes.router)
app.include_router(ui.router, include_in_schema=False)
app.include_router(container_logs.router, include_in_schema=False)
app.include_router(stats.router, include_in_schema=False)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
