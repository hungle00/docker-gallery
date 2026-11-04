import docker
from fastapi import APIRouter, HTTPException
from app.services.docker_client import client

router = APIRouter(prefix="/api/networks", tags=["Networks"])

@router.get("")
def list_networks():
    networks = client.networks.list()
    return [
        {
            "id": net.id[:12],
            "name": net.name,
            "driver": net.attrs.get("Driver"),
            "scope": net.attrs.get("Scope"),
        }
        for net in networks
    ]

@router.get("/{network_id}")
def inspect_network(network_id: str):
    try:
        net = client.networks.get(network_id)
        return net.attrs
    except docker.errors.NotFound as e:
        raise HTTPException(status_code=404, detail="Network không tồn tại") from e
    except docker.errors.DockerException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
