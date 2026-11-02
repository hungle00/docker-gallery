import asyncio
import docker
from fastapi import APIRouter, Form, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from services.docker_client import client

router = APIRouter(prefix="/api/containers", tags=["Containers"])
ui_router = APIRouter(tags=["Container UI"])

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

def _apply_container_action(container_id: str, action: str) -> None:
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

def _remove_container(container_id: str) -> None:
    try:
        container = client.containers.get(container_id)
        container.remove(force=True)
    except docker.errors.NotFound as e:
        raise HTTPException(status_code=404, detail="Container không tồn tại") from e
    except docker.errors.DockerException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

def render_container_table(request: Request) -> HTMLResponse:
    from main import templates

    try:
        docker_containers = client.containers.list(all=True)
        container_list = [
            {
                "id": c.id[:12],
                "name": c.name,
                "status": c.status,
                "image": c.image.tags[0] if c.image.tags else "<none>",
            }
            for c in docker_containers
        ]
    except docker.errors.DockerException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return templates.TemplateResponse(
        request,
        "partials/container_table.html",
        {"containers": container_list},
    )

@router.post("/{container_id}/{action}")
def container_action(container_id: str, action: str):
    _apply_container_action(container_id, action)
    return {"status": "success", "action": action, "container_id": container_id}

@ui_router.post("/ui/containers/{container_id}/{action}", response_class=HTMLResponse)
def container_action_for_ui(request: Request, container_id: str, action: str):
    _apply_container_action(container_id, action)
    return render_container_table(request)

@router.delete("/{container_id}")
def remove_container(container_id: str):
    _remove_container(container_id)
    return {"status": "success", "message": f"Đã xóa container {container_id}"}

@ui_router.delete("/ui/containers/{container_id}", response_class=HTMLResponse)
def remove_container_for_ui(request: Request, container_id: str):
    _remove_container(container_id)
    return render_container_table(request)

@router.websocket("/{container_id}/logs")
async def container_logs_ws(websocket: WebSocket, container_id: str):
    await websocket.accept()
    try:
        container = client.containers.get(container_id)
        logs_stream = container.logs(stream=True, follow=True, tail=100)
        for chunk in logs_stream:
            log_line = chunk.decode("utf-8", errors="ignore")
            await websocket.send_text(log_line)
            await asyncio.sleep(0.01)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_text(f"Lỗi: {str(e)}")
        await websocket.close()
