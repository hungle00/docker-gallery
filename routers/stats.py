import asyncio
import json
import docker
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.docker_client import client

router = APIRouter(prefix="/ws", tags=["Stats"])

@router.websocket("/containers/{container_id}/stats")
async def container_stats_ws(websocket: WebSocket, container_id: str):
    await websocket.accept()
    try:
        container = client.containers.get(container_id)
        stats_generator = container.stats(stream=True, decode=True)
        
        for stats in stats_generator:
            cpu_percent = 0.0
            cpu_stats = stats.get("cpu_stats", {})
            precpu_stats = stats.get("precpu_stats", {})
            
            cpu_delta = cpu_stats.get("cpu_usage", {}).get("total_usage", 0) - \
                        precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
            system_delta = cpu_stats.get("system_cpu_usage", 0) - \
                           precpu_stats.get("system_cpu_usage", 0)
            
            num_cpus = cpu_stats.get("online_cpus", len(cpu_stats.get("cpu_usage", {}).get("percpu_usage", [])))
            
            if system_delta > 0 and cpu_delta > 0 and num_cpus > 0:
                cpu_percent = (cpu_delta / system_delta) * num_cpus * 100.0

            memory_stats = stats.get("memory_stats", {})
            mem_usage = memory_stats.get("usage", 0)
            mem_limit = memory_stats.get("limit", 1)
            mem_percent = (mem_usage / mem_limit) * 100.0

            payload = {
                "cpu_percent": round(cpu_percent, 2),
                "memory_usage_mb": round(mem_usage / (1024 * 1024), 2),
                "memory_limit_mb": round(mem_limit / (1024 * 1024), 2),
                "memory_percent": round(mem_percent, 2)
            }

            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(0.5)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_text(json.dumps({"error": str(e)}))
        await websocket.close()
