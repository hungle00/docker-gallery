from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from routers import containers, images, networks, stats, volumes
from services.docker_client import client

app = FastAPI(title="Lightweight Docker Dashboard", version="1.0")

# Mount Static & Templates
# app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Register Routers
app.include_router(containers.router)
app.include_router(containers.ui_router)
app.include_router(images.router)
app.include_router(networks.router)
app.include_router(stats.router)
app.include_router(volumes.router)

# Page Routes
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/partials/containers-table")
def containers_table_partial(request: Request):
    """Render the container table HTML fragment for HTMX."""
    return containers.render_container_table(request)

@app.get("/containers/{container_id}/detail")
def container_detail_page(request: Request, container_id: str):
    return templates.TemplateResponse(
        request,
        "container_detail.html",
        {"container_id": container_id},
    )

@app.get("/containers/{container_id}/logs")
def container_logs_page(request: Request, container_id: str):
    return templates.TemplateResponse(
        request,
        "container_logs.html",
        {"container_id": container_id},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
