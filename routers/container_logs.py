import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services.docker_client import client

router = APIRouter(prefix="/api/containers", tags=["Container Logs"])


def _next_log_chunk(logs_stream):
    try:
        return next(logs_stream)
    except StopIteration:
        return None


@router.websocket("/{container_id}/logs")
async def container_logs_ws(websocket: WebSocket, container_id: str):
    await websocket.accept()
    logs_stream = None
    try:
        container = await asyncio.to_thread(client.containers.get, container_id)
        logs_stream = await asyncio.to_thread(
            container.logs,
            stream=True,
            follow=True,
            tail=100,
        )
        while True:
            chunk = await asyncio.to_thread(_next_log_chunk, logs_stream)
            if chunk is None:
                break
            await websocket.send_text(chunk.decode("utf-8", errors="ignore"))
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_text(f"Lỗi: {e}")
        await websocket.close()
    finally:
        if logs_stream is not None:
            await asyncio.to_thread(logs_stream.close)
