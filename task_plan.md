# B.L.A.S.T. Task Plan: Reverse Cam Automation

## Project Status: COMPLETED (All Phases Verified)

---

## Phases & Checklists

### 🟢 Protocol 0: Initialization
- [x] Create project memory files (`task_plan.md`, `findings.md`, `progress.md`, `gemini.md`)
- [x] Analyze existing codebase (`reverse_cam.ino`, `pi_config.py`)
- [x] Enforce Execution Halt: No tools or code in `tools/` until Discovery is completed and Data Schema is approved

### 🏗️ Phase 1: B - Blueprint (Vision & Logic)
- [x] Submit 5 Discovery Questions to the user & capture responses:
  - [x] 1. North Star: Reverse parking support device with proximity sensor and camera.
  - [x] 2. Integrations: BLE only for now, load UUIDs from `.env`, future ESP32 network calls.
  - [x] 3. Source of Truth: Local storage on Pi & ESP32, future VPS with specialized cube data model.
  - [x] 4. Delivery Payload: Terminal-based UI on Pi (future web GUI), buzzer activations on ESP32 (future rocker switch override).
  - [x] 5. Behavioral Rules: Researched automotive reverse proximity standards (ISO 17386 / MALSO).
- [x] Conduct research: ISO 17386 standards, hysteresis banding (20mm), 3-sample median filter, failsafe stale data timeout (500ms).
- [x] Define JSON Data Schemas in `gemini.md`:
  - `ReverseCamSettings` (8-parameter GATT configuration)
  - `ReverseCamTelemetry` (Real-time stream with hysteresis and status)
  - `ParkingSessionFact` (Cube data model fact table for local/VPS analytical storage)
- [x] Created `.env` and `.env.example` containing firmware UUIDs and VPS placeholders.

### ⚡ Phase 2: L - Link (Connectivity)
- [x] Implement `.env` loader verification script
- [x] Build minimal handshake tool `tools/ble_link_test.py` to test environment variables and adapter readiness
- [x] Verified Bluetooth adapter operational status and `.tmp/ble_link_status.json` output

### ⚙️ Phase 3: A - Architect (The 3-Layer Build)
- [x] **Layer 1: Architecture (`architecture/`)**:
  - `sop_ble_client.md`: BLE connection, reconnect, and GATT characteristic read/write.
  - `sop_proximity_filter.md`: Hysteresis and median filtering logic.
  - `sop_session_logger.md`: Local JSON Lines analytical logging adhering to cube schema.
  - `sop_terminal_ui.md`: Non-blocking terminal HUD rendering & cross-platform encoding.
- [x] **Layer 2: Navigation**: `reverse_cam_runner.py` main orchestrator.
- [x] **Layer 3: Tools (`tools/`)**:
  - `tools/ble_link_test.py`: BLE handshake and ping.
  - `tools/ble_manager.py`: Async BLE interface with `.env` loader and simulation fallback.
  - `tools/proximity_filter.py`: Median filter + hysteresis state machine.
  - `tools/session_logger.py`: Local cube data model session logger.
  - `tools/terminal_hud.py`: Terminal HUD visualizer with ANSI colors.
  - `tools/test_proximity_filter.py`: Unit test suite (Passed).
  - `tools/test_session_logger.py`: Unit test suite (Passed).
- [x] **Self-Annealing Cycle**: Analyzed Windows stdout CP1252 character map limitation, patched `tools/terminal_hud.py`, verified with simulation run, and updated `architecture/sop_terminal_ui.md`.

### ✨ Phase 4: S - Stylize (Refinement & UI)
- [x] Designed rich terminal HUD with colorized proximity gauge (`SAFE`, `FAR`, `MID`, `CLOSE`, `CRITICAL STOP`).
- [x] Added real-time session telemetry summary (minimum clearance, solid tone count, samples processed).
- [x] Validated interactive exit and clean data flushing.

### 🛰️ Phase 5: T - Trigger (Deployment)
- [x] Created Raspberry Pi systemd autostart service: `deploy/reverse-cam.service`.
- [x] Created automated installation script: `deploy/setup_pi.sh`.
- [x] Created batch / shell convenience launchers: `run_hud.bat`, `start_reverse_cam.sh`.
- [x] Documented in `gemini.md` Maintenance Log.

### 🔮 Phase 6: Future Roadmap & Architectural Extensions

#### 4. Automotive Resiliency & Fault Tolerance: Automatic BLE Reconnect Loop with Exponential Backoff
- **Current State**: If Bluetooth connectivity drops (e.g., ignition cycle or momentary RF interference), the watchdog properly marks telemetry as `DISCONNECTED` / `STALE`, but the runner does not attempt an active background reconnect, requiring a manual systemd or runner restart.
- **Target Best Practice**: Trigger an asynchronous background reconnect supervisor whenever the link breaks, automatically recovering connectivity without requiring a driver or service restart.
- **Implementation Plan**:
  - [ ] **State Machine & Status Callbacks**: Expand `tools/ble_manager.py` connection states: `CONNECTED`, `DISCONNECTED`, `RECONNECTING_BACKOFF`.
  - [ ] **Exponential Backoff Algorithm**: Implement reconnect attempts starting at 1.0s, doubling up to a maximum cap (e.g., 30.0s) with $\pm 20\%$ jitter to prevent RF storming during vehicle ignition cycling:
    $$t_{\text{backoff}} = \min(t_{\text{max}}, t_{\text{base}} \times 2^{\text{attempt}}) \pm \text{jitter}$$
  - [ ] **Non-Blocking Task Supervisor**: In `reverse_cam_runner.py`, spawn `asyncio.create_task(reconnect_supervisor())` on BLE disconnect event so the HUD continues rendering the status `RECONNECTING (Attempt N)...` without freezing user interaction.
  - [ ] **Auto-Resubscription**: Re-establish GATT notifications on `DISTANCE_CHAR_UUID` and query `SETTINGS_CHAR_UUID` on successful reconnection before transitioning back to `HEALTHY`.
  - [ ] **Automated Testing**: Add unit test in `tests/test_ble_link.py` mocking connection drop and verifying exponential backoff intervals and reconnection callback triggers.

#### 5. Cloud / VPS Telemetry Synchronization: Offline-First Store-and-Forward
- **Current State**: `.env.example` declares `SERVER_LOG_API_URL` and `SERVER_API_KEY`, but `tools/session_logger.py` only writes records locally with `"sync_status": "LOCAL_STORED"`.
- **Target Best Practice**: Implement an offline-first background synchronization worker (`sync_pending_sessions()`) that pushes completed parking sessions when Wi-Fi or LTE connectivity is present, transitioning session records from `LOCAL_STORED` to `VPS_SYNCED`.
- **Implementation Plan**:
  - [ ] **Sync Engine Method**: Add `sync_pending_sessions(batch_size=10, timeout=5.0)` to `tools/session_logger.py` using `urllib.request` (zero third-party dependencies) or `requests` if available.
  - [ ] **Authentication & Payload**: Format payload conforming to `gemini.md` Schema C (`ParkingSessionFact`) with HTTP header `Authorization: Bearer <SERVER_API_KEY>` or `X-API-Key`.
  - [ ] **Atomic File Update**: Read `.jsonl`, identify entries with `LOCAL_STORED` or `SYNC_PENDING`, transmit to `SERVER_LOG_API_URL`, and atomically rewrite or update sync flags to `VPS_SYNCED` with `synced_at_iso` timestamp upon HTTP 200/201 response.
  - [ ] **Network Connectivity Guard**: Probe endpoint reachability with short timeout (e.g., 2.0s) before sending data to avoid blocking or logging spam while vehicle is out of Wi-Fi/cellular range.
  - [ ] **Background Scheduling**: Trigger sync check opportunistically on session completion (`finalize_session()`) and periodically (e.g. every 5 minutes) via `asyncio` background task.
  - [ ] **Automated Testing**: Add mock HTTP server tests in `tests/test_session_logger.py` testing successful sync, network failure handling, and idempotent status updates.
