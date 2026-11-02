# Docker Gallery

A lightweight, modern, and self-hosted Docker management dashboard built with **FastAPI**, **HTMX**, **Alpine.js**, and **Tailwind CSS**.

Designed for simplicity, this project requires no complex Node.js frontend toolchain, consumes minimal system resources, and provides smooth real-time monitoring capabilities.

## Tech Stack
- Backend: Python, FastAPI, Uvicorn, Docker Python SDK

- Frontend: Tailwind CSS (CDN), HTMX, Alpine.js, Chart.js

---

## Key Features

- **Containers Management:** List, start, stop, restart, remove containers, and inspect their configurations.
- **Real-time Logs:** Stream container logs directly via WebSockets.
- **Resource Observability:** Monitor real-time **CPU** and **Memory** usage percentages with live charts (powered by Chart.js & WebSockets).
- **Images Management:** List, pull new images from registries, and remove images.
- **Volumes Management:** List, inspect, and remove Docker volumes.
- **Modern UI:** Inspired by Docker Desktop, featuring a sleek Tailwind CSS layout combined with HTMX for fast, seamless page updates without full reloads.

---
