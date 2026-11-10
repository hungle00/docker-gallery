import docker
from fastapi import APIRouter, HTTPException
from app.services.docker_client import client

router = APIRouter(prefix="/api/networks", tags=["Networks"])

BUILTIN_NETWORKS = {"bridge", "host", "none"}


def network_containers(network_attrs):
    return [
        {
            "id": container_id[:12],
            "name": container.get("Name", ""),
            "ipv4_address": container.get("IPv4Address", ""),
            "ipv6_address": container.get("IPv6Address", ""),
        }
        for container_id, container in (network_attrs.get("Containers") or {}).items()
    ]


def is_builtin_network(network_name: str) -> bool:
    return network_name in BUILTIN_NETWORKS


def list_networks():
    networks = client.networks.list()
    for network in networks:
        network.reload()
    return networks


@router.get("")
def get_networks():
    try:
        networks = list_networks()
        return [
            {
                "id": net.id[:12],
                "name": net.name,
                "driver": net.attrs.get("Driver"),
                "scope": net.attrs.get("Scope"),
                "containers": network_containers(net.attrs),
                "is_builtin": is_builtin_network(net.name),
            }
            for net in networks
        ]
    except docker.errors.DockerException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{network_id}")
def inspect_network(network_id: str):
    try:
        net = client.networks.get(network_id)
        return net.attrs
    except docker.errors.NotFound as e:
        raise HTTPException(status_code=404, detail="Network không tồn tại") from e
    except docker.errors.DockerException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


def delete_network(network_id: str) -> None:
    try:
        network = client.networks.get(network_id)
        if is_builtin_network(network.name):
            raise HTTPException(
                status_code=400,
                detail="Không thể xóa network mặc định của Docker",
            )
        network.remove()
    except HTTPException:
        raise
    except docker.errors.NotFound as e:
        raise HTTPException(status_code=404, detail="Network không tồn tại") from e
    except docker.errors.DockerException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/{network_id}")
def remove_network(network_id: str):
    delete_network(network_id)
    return {"status": "success", "message": f"Đã xóa network {network_id}"}
