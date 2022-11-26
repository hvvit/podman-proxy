test:
	PODMAN_PROXY_USERNAME="admin" PODMAN_PROXY_PASSWORD="test" python3 main.py
build:
	pip install pyinstaller
	pyinstaller --onefile main.py