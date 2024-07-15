FROM debian:bookworm-slim

RUN apt update && apt upgrade -y
RUN apt install -y python3-venv python3-pip git

# Install debian-package-collector
COPY dist/*.whl /etc/debian-package-collector/
RUN python3 -m venv venv
RUN venv/bin/pip install /etc/debian-package-collector/*.whl

# Start debian-package-collector
ENTRYPOINT venv/bin/python3 venv/bin/debian-package-collector.py "$@"
