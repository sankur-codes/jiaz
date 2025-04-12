# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system deps and pyinstaller
RUN apt-get update && apt-get install -y \
    bash \
    build-essential \
    git \
    && pip install --no-cache-dir pyinstaller

ENTRYPOINT ["/bin/bash"]
