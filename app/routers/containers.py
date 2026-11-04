import docker
from fastapi import APIRouter, HTTPException
from app.services.docker_client import client

router = APIRouter(prefix="/api/containers", tags=["Containers"])

@router.get("")
def list_containers():
    containers = client.containers.list(all=True)
    return [
        {
            "id": c.id[:12],
            "name": c.name,
            "status": c.status,
            "image": c.image.tags[0] if c.image.tags else "<none>",
            "created": c.attrs["Created"],
        }
        for c in containers
    ]

@router.get("/{container_id}")
def inspect_container(container_id: str):
    try:
        container = client.containers.get(container_id)
        attrs = container.attrs
        return {
            "id": container.id[:12],
            "name": container.name,
            "status": container.status,
            "config": attrs.get("Config", {}),
            "ports": attrs.get("NetworkSettings", {}).get("Ports", {}),
            "mounts": attrs.get("Mounts", []),
            "networks": attrs.get("NetworkSettings", {}).get("Networks", {}),
        }
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Container không tồn tại")

def perform_container_action(container_id: str, action: str) -> None:
    if action not in {"start", "stop", "restart"}:
        raise HTTPException(status_code=400, detail="Action không hợp lệ")

    try:
        container = client.containers.get(container_id)
        if action == "start":
            container.start()
        elif action == "stop":
            container.stop()
        else:
            container.restart()
    except docker.errors.NotFound as e:
        raise HTTPException(status_code=404, detail="Container không tồn tại") from e
    except docker.errors.DockerException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

def delete_container(container_id: str) -> None:
    try:
        container = client.containers.get(container_id)
        container.remove(force=True)
    except docker.errors.NotFound as e:
        raise HTTPException(status_code=404, detail="Container không tồn tại") from e
    except docker.errors.DockerException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/{container_id}/{action}")
def container_action(container_id: str, action: str):
    perform_container_action(container_id, action)
    return {"status": "success", "action": action, "container_id": container_id}

@router.delete("/{container_id}")
def remove_container(container_id: str):
    delete_container(container_id)
    return {"status": "success", "message": f"Đã xóa container {container_id}"}
