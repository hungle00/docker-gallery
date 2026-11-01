import docker

try:
    client = docker.from_env()
except Exception as e:
    print(f"Không thể kết nối Docker Daemon: {e}")
    exit(1)
