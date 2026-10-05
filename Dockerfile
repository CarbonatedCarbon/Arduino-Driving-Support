# Multi-arch compatible slim Python base (supports Raspberry Pi ARM64/v7 and PC x86_64)
FROM python:3.12-slim-bookworm

# Prevent Python from writing .pyc and enable unbuffered terminal streaming
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TERM=xterm-256color

# Install system dependencies: BlueZ, D-Bus, glib for BLE, and git/curl for graphify
RUN apt-get update && apt-get install -y --no-install-recommends \
    bluez \
    dbus \
    libglib2.0-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cache dependency layer
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application codebase
COPY . .

# Ensure scripts have executable permissions and directories exist
RUN chmod +x /app/docker-entrypoint.sh \
    && mkdir -p /app/data /app/.tmp

# Define volumes for telemetry data persistence
VOLUME ["/app/data", "/app/.tmp"]

ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command: start ReverseCam HUD runner
CMD ["python", "reverse_cam_runner.py"]
