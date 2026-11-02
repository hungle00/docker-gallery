import docker
from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from services.docker_client import client

router = APIRouter(tags=["Images"])

@router.get("/images", response_class=HTMLResponse)
def images_page(request: Request):
    from main import templates
    return templates.TemplateResponse(request, "images.html")

@router.get("/api/images/table")
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
    except Exception:
        image_list = []
    return templates.TemplateResponse(
        request,
        "partials/image_table.html",
        {"images": image_list}
    )

@router.delete("/api/images/{image_id}")
def remove_image(image_id: str):
    try:
        client.images.remove(image_id, force=True)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
