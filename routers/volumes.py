import docker
from fastapi import APIRouter, HTTPException
from services.docker_client import client

router = APIRouter(prefix="/api/volumes", tags=["Volumes"])

def delete_volume(volume_name: str) -> None:
    try:
        vol = client.volumes.get(volume_name)
        vol.remove(force=True)
    except docker.errors.NotFound as e:
        raise HTTPException(status_code=404, detail="Volume không tồn tại") from e
    except docker.errors.DockerException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.delete("/{volume_name}")
def remove_volume(volume_name: str):
    delete_volume(volume_name)
    return {"status": "success", "message": f"Đã xóa volume {volume_name}"}
