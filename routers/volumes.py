import docker
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from services.docker_client import client

router = APIRouter(tags=["Volumes"])

@router.get("/volumes", response_class=HTMLResponse)
def volumes_page(request: Request):
    from main import templates
    return templates.TemplateResponse(request, "volumes.html")

@router.get("/api/volumes/table")
def volumes_table(request: Request):
    from main import templates
    try:
        volumes = client.volumes.list()
        volume_list = [
            {
                "name": v.name,
                "driver": v.attrs.get("Driver"),
                "scope": v.attrs.get("Scope"),
                "mountpoint": v.attrs.get("Mountpoint", "")
            }
            for v in volumes
        ]
    except Exception:
        volume_list = []
    return templates.TemplateResponse(
        request,
        "partials/volume_table.html",
        {"volumes": volume_list}
    )

@router.delete("/api/volumes/{volume_name}")
def remove_volume(volume_name: str):
    try:
        vol = client.volumes.get(volume_name)
        vol.remove(force=True)
        return {"status": "success", "message": f"Đã xóa volume {volume_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
