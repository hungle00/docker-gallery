import docker
from fastapi import APIRouter, HTTPException
from services.docker_client import client

router = APIRouter(prefix="/api/images", tags=["Images"])

@router.get("")
def list_images():
    images = client.images.list()
    return [
        {
            "id": img.id[:12],
            "tags": img.tags,
            "size": img.attrs.get("Size", 0),
            "created": img.attrs.get("Created", ""),
        }
        for img in images
    ]

@router.post("/pull")
def pull_image(image_name: str):
    try:
        client.images.pull(image_name)
        return {"status": "success", "message": f"Đã tải thành công image {image_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{image_id}")
def remove_image(image_id: str):
    try:
        client.images.remove(image_id, force=True)
        return {"status": "success", "message": f"Đã xóa image {image_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
