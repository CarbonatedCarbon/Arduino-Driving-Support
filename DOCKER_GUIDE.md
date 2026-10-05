# Docker Guide for ReverseCam

This document explains how to build, run, and deploy the ReverseCam Python application using Docker and Docker Compose.

---

## Architecture Overview

```
                      +---------------------------------------+
                      |             Host Machine              |
                      |  (Raspberry Pi, Linux PC, Windows)    |
                      +---------------------------------------+
                                          |
                      D-Bus / Host Net    |   Volumes
                      (/var/run/dbus)     |   (./data, ./.tmp, ./.env)
                                          v
                      +---------------------------------------+
                      |         Docker Container              |
                      |       (python:3.12-slim)              |
                      |                                       |
                      |  - BlueZ / D-Bus / Bleak              |
                      |  - reverse_cam_runner.py              |
                      |  - ProximityFilter (Hysteresis)       |
                      |  - Terminal HUD Visualizer            |
                      |  - Session Telemetry Logger           |
                      +---------------------------------------+
                                          |
                                          | BLE GATT
                                          v
                      +---------------------------------------+
                      |        ESP32 ReverseCam Node          |
                      |     (HC-SR04 Sensor + Buzzer)         |
                      +---------------------------------------+
```

---

## Quick Start

### 1. Build the Docker Image
```bash
docker compose build
# Or with standard docker CLI:
docker build -t reverse-cam:latest .
```

---

### 2. Running in Simulation Mode (No Hardware Needed)
Ideal for testing on Windows, macOS, or Linux PCs without an ESP32 or Bluetooth adapter:

```bash
docker compose run --rm reverse-cam-sim
```
*Or using standalone `docker`:*
```bash
docker run -it --rm \
  -v ${PWD}/data:/app/data \
  -v ${PWD}/.tmp:/app/.tmp \
  reverse-cam:latest python reverse_cam_runner.py --simulate
```

---

### 3. Running with Physical BLE on Raspberry Pi / Linux Host
When deployed to a Raspberry Pi or Linux system with a Bluetooth controller:

```bash
docker compose up reverse-cam
```

*Requirements for host BLE access inside Docker:*
- Host BlueZ daemon running (`sudo systemctl start bluetooth`).
- D-Bus socket mounted: `/var/run/dbus/system_bus_socket:/var/run/dbus/system_bus_socket`.
- Host networking: `--net=host` / `network_mode: host`.
- Elevated capability: `--privileged` or `--cap-add=NET_ADMIN`.

---

### 4. Running the Interactive BLE Configuration Tool
To connect to the ESP32 and tweak distance thresholds or buzzer volume in real-time:

```bash
docker compose run --rm config-tool
```

---

### 5. Running the Test Suite Inside Docker
To verify the median filtering, hysteresis transitions, and session logger:

```bash
docker compose run --rm test
```

---

### 6. Running Graphify Inside Docker
To generate or query the codebase knowledge graph inside the container:

```bash
# Build knowledge graph for current project:
docker compose run --rm graphify

# Query the graph:
docker compose run --rm graphify graphify query "How does proximity filtering work?"
```

---

## File Structure & Volumes

- `/app/.env`: Bluetooth UUIDs and server endpoints (copied automatically from `.env.example` if not present).
- `/app/data/`: Persistent parking session metrics (`data/parking_sessions.jsonl`).
- `/app/.tmp/`: Real-time telemetry log buffers (`.tmp/session_telemetry.jsonl`).

---

## Troubleshooting

### Error: `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`
- **Cause**: The Docker Desktop application / background engine is not running on Windows.
- **Solution**:
  1. Open the Windows Start menu.
  2. Search for **Docker Desktop** and launch it.
  3. Wait until the whale icon in your Windows notification tray / system tray turns solid (status shows "Docker Desktop is running").
  4. Re-run your command or Compose task.
