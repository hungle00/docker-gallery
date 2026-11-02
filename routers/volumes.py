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
@router.get("/partials/volumes-table", include_in_schema=False)
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
    except docker.errors.DockerException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return templates.TemplateResponse(
        request,
        "partials/volume_table.html",
        {"volumes": volume_list}
    )

def _remove_volume(volume_name: str) -> None:
    try:
        vol = client.volumes.get(volume_name)
        vol.remove(force=True)
    except docker.errors.NotFound as e:
        raise HTTPException(status_code=404, detail="Volume không tồn tại") from e
    except docker.errors.DockerException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.delete("/api/volumes/{volume_name}")
def remove_volume(volume_name: str):
    _remove_volume(volume_name)
    return {"status": "success", "message": f"Đã xóa volume {volume_name}"}

@router.delete("/ui/volumes/{volume_name}", response_class=HTMLResponse)
def remove_volume_for_ui(request: Request, volume_name: str):
    _remove_volume(volume_name)
    return volumes_table(request)
