import docker
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from app.services.docker_client import client

from app.routers.containers import delete_container, perform_container_action
from app.routers.images import delete_image
from app.routers.networks import (
    delete_network,
    is_builtin_network,
    list_networks,
    network_containers,
)
from app.routers.volumes import delete_volume

router = APIRouter(tags=["UI"])


def _templates():
    from app.main import templates

    return templates


def render_container_table(request: Request) -> HTMLResponse:
    try:
        docker_containers = client.containers.list(all=True)
        container_list = [
            {
                "id": container.id[:12],
                "name": container.name,
                "status": container.status,
                "image": container.image.tags[0] if container.image.tags else "<none>",
            }
            for container in docker_containers
        ]
    except docker.errors.DockerException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return _templates().TemplateResponse(
        request,
        "partials/container_table.html",
        {"containers": container_list},
    )


def render_image_table(request: Request) -> HTMLResponse:
    try:
        images = client.images.list()
        image_list = [
            {
                "id": image.id[:12],
                "tags": image.tags if image.tags else ["<none>:<none>"],
                "size": round(image.attrs.get("Size", 0) / (1024 * 1024), 2),
                "created": image.attrs.get("Created", ""),
            }
            for image in images
        ]
    except docker.errors.DockerException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return _templates().TemplateResponse(
        request,
        "partials/image_table.html",
        {"images": image_list},
    )


def render_volume_table(request: Request) -> HTMLResponse:
    try:
        volumes = client.volumes.list()
        volume_list = [
            {
                "name": volume.name,
                "driver": volume.attrs.get("Driver"),
                "scope": volume.attrs.get("Scope"),
                "mountpoint": volume.attrs.get("Mountpoint", ""),
            }
            for volume in volumes
        ]
    except docker.errors.DockerException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return _templates().TemplateResponse(
        request,
        "partials/volume_table.html",
        {"volumes": volume_list},
    )


def render_network_table(request: Request) -> HTMLResponse:
    try:
        networks = list_networks()
        network_list = [
            {
                "id": network.id[:12],
                "name": network.name,
                "driver": network.attrs.get("Driver"),
                "scope": network.attrs.get("Scope"),
                "containers": network_containers(network.attrs),
                "is_builtin": is_builtin_network(network.name),
            }
            for network in networks
        ]
    except docker.errors.DockerException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return _templates().TemplateResponse(
        request,
        "partials/network_table.html",
        {"networks": network_list},
    )


@router.get("/")
def home(request: Request):
    return _templates().TemplateResponse(request, "index.html")


@router.get("/images", response_class=HTMLResponse)
def images_page(request: Request):
    return _templates().TemplateResponse(request, "images.html")


@router.get("/volumes", response_class=HTMLResponse)
def volumes_page(request: Request):
    return _templates().TemplateResponse(request, "volumes.html")


@router.get("/networks", response_class=HTMLResponse)
def networks_page(request: Request):
    return _templates().TemplateResponse(request, "networks.html")


@router.get("/networks/{network_id}", response_class=HTMLResponse)
def network_detail_page(request: Request, network_id: str):
    try:
        network = client.networks.get(network_id)
        network.reload()
    except docker.errors.NotFound as e:
        raise HTTPException(status_code=404, detail="Network không tồn tại") from e
    except docker.errors.DockerException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    attrs = network.attrs
    return _templates().TemplateResponse(
        request,
        "network_detail.html",
        {
            "network": {
                "id": network.id,
                "name": network.name,
                "created": attrs.get("Created", ""),
                "driver": attrs.get("Driver", ""),
                "scope": attrs.get("Scope", ""),
                "internal": attrs.get("Internal", False),
                "attachable": attrs.get("Attachable", False),
                "ingress": attrs.get("Ingress", False),
                "enable_ipv6": attrs.get("EnableIPv6", False),
                "ipam": attrs.get("IPAM") or {},
                "options": attrs.get("Options") or {},
                "labels": attrs.get("Labels") or {},
                "containers": network_containers(attrs),
            }
        },
    )


@router.get("/partials/containers-table", response_class=HTMLResponse)
def containers_table_partial(request: Request):
    return render_container_table(request)


@router.get("/partials/images-table", response_class=HTMLResponse)
def images_table_partial(request: Request):
    return render_image_table(request)


@router.get("/partials/volumes-table", response_class=HTMLResponse)
def volumes_table_partial(request: Request):
    return render_volume_table(request)


@router.get("/partials/networks-table", response_class=HTMLResponse)
def networks_table_partial(request: Request):
    return render_network_table(request)


@router.delete("/ui/networks/{network_id}", response_class=HTMLResponse)
def remove_network_for_ui(request: Request, network_id: str):
    delete_network(network_id)
    return render_network_table(request)


@router.post(
    "/ui/containers/{container_id}/{action}",
    response_class=HTMLResponse,
)
def container_action_for_ui(request: Request, container_id: str, action: str):
    perform_container_action(container_id, action)
    return render_container_table(request)


@router.delete(
    "/ui/containers/{container_id}",
    response_class=HTMLResponse,
)
def remove_container_for_ui(request: Request, container_id: str):
    delete_container(container_id)
    return render_container_table(request)


@router.delete("/ui/images/{image_id}", response_class=HTMLResponse)
def remove_image_for_ui(request: Request, image_id: str):
    delete_image(image_id)
    return render_image_table(request)


@router.post("/ui/images/pull", response_class=HTMLResponse)
def pull_image_for_ui(request: Request, image_name: str = Form(...)):
    try:
        client.images.pull(image_name)
    except docker.errors.DockerException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return render_image_table(request)


@router.delete("/ui/volumes/{volume_name}", response_class=HTMLResponse)
def remove_volume_for_ui(request: Request, volume_name: str):
    delete_volume(volume_name)
    return render_volume_table(request)


@router.get("/containers/{container_id}/detail", response_class=HTMLResponse)
def container_detail_page(request: Request, container_id: str):
    return _templates().TemplateResponse(
        request,
        "container_detail.html",
        {"container_id": container_id},
    )


@router.get("/containers/{container_id}/logs", response_class=HTMLResponse)
def container_logs_page(request: Request, container_id: str):
    return _templates().TemplateResponse(
        request,
        "container_logs.html",
        {"container_id": container_id},
    )
