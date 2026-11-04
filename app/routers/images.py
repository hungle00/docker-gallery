import docker
from fastapi import APIRouter, HTTPException
from app.services.docker_client import client

router = APIRouter(prefix="/api/images", tags=["Images"])

def delete_image(image_id: str) -> None:
    try:
        client.images.remove(image_id, force=True)
    except docker.errors.ImageNotFound as e:
        raise HTTPException(status_code=404, detail="Image không tồn tại") from e
    except docker.errors.DockerException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.delete("/{image_id}")
def remove_image(image_id: str):
    delete_image(image_id)
    return {"status": "success"}
