import docker
from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from services.docker_client import client

router = APIRouter(tags=["Images"])

@router.get("/images", response_class=HTMLResponse)
def images_page(request: Request):
    from main import templates
    return templates.TemplateResponse(request, "images.html")

@router.get("/api/images/table", include_in_schema=False)
@router.get("/partials/images-table")
def images_table(request: Request):
    from main import templates
    try:
        images = client.images.list()
        image_list = [
            {
                "id": img.id[:12],
                "tags": img.tags if img.tags else ["<none>:<none>"],
                "size": round(img.attrs.get("Size", 0) / (1024 * 1024), 2),
                "created": img.attrs.get("Created", "")
            }
            for img in images
        ]
    except docker.errors.DockerException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return templates.TemplateResponse(
        request,
        "partials/image_table.html",
        {"images": image_list}
    )

def _remove_image(image_id: str) -> None:
    try:
        client.images.remove(image_id, force=True)
    except docker.errors.ImageNotFound as e:
        raise HTTPException(status_code=404, detail="Image không tồn tại") from e
    except docker.errors.DockerException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.delete("/api/images/{image_id}")
def remove_image(image_id: str):
    _remove_image(image_id)
    return {"status": "success"}

@router.delete("/ui/images/{image_id}", response_class=HTMLResponse)
def remove_image_for_ui(request: Request, image_id: str):
    _remove_image(image_id)
    return images_table(request)

@router.post("/ui/images/pull", response_class=HTMLResponse)
def pull_image_for_ui(request: Request, image_name: str = Form(...)):
    try:
        client.images.pull(image_name)
    except docker.errors.DockerException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return images_table(request)
