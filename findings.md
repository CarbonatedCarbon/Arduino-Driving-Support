# Project Findings & Discoveries

## 1. Existing System Architecture

### Hardware / Firmware (`reverse_cam.ino`)
- **Microcontroller**: ESP32
- **Peripheral Pins**:
  - `I2C_SDA_PIN`: GPIO 21
  - `I2C_SCL_PIN`: GPIO 22
  - `BUZZER_PIN`: GPIO 33 (driven by LEDC PWM, 2 kHz frequency, 8-bit resolution)
- **Distance Sensor**:
  - Communicates via I2C at address `0x74`
  - Register `0x10` written with `0xB0` to trigger reading; data read from register `0x02` (2 bytes, formula: `buf[0] * 256 + buf[1] + 10` mm)
- **Bluetooth Low Energy (BLE)**:
  - Device Name: `ReverseCam`
  - Service UUID: `4fafc201-1fb5-459e-8fcc-c5c9c331914b`
  - Settings Characteristic UUID: `beb5483e-36e1-4688-b7f5-ea07361b26a8` (Read/Write, CSV format with 8 values)
  - Distance Characteristic UUID: `1c95d5e3-d8f7-413a-bf3d-7a2e5d7be87e` (Read/Notify, string distance in mm)
- **Settings Parameters (CSV Order)**:
  1. `DISTANCE_MAX_WARNING` (Default: 800 mm)
  2. `DISTANCE_MID_ZONE` (Default: 400 mm)
  3. `DISTANCE_CLOSE_ZONE` (Default: 150 mm)
  4. `DISTANCE_SOLID_TONE` (Default: 30 mm)
  5. `BEEP_FAR` (Default: 600 ms)
  6. `BEEP_MID` (Default: 300 ms)
  7. `BEEP_CLOSE` (Default: 100 ms)
  8. `buzzerVolume` (Default: 8%, 0-100%)

### Client Configuration Script (`pi_config.py`)
- Python 3.7+ async BLE client using `bleak`.
- Scans for `ReverseCam`, pairs over GATT.
- Console text interface for setting values and reading live distance notifications.

---

## 2. Research on Automotive Reverse Proximity Sensors (ISO 17386 / MALSO)

### Standards & Industry Practice (ISO 17386 - Maneuvering Aids for Low Speed Operation)
1. **Auditory Warning Progression**:
   - Industry standards define increasing beep repetition rate as proximity closes.
   - Continuous tone signifies the "Stop / Danger" barrier.
   - **Continuous Tone Distance Benchmark**: OEM systems universally trigger solid tone between **200 mm and 300 mm** (20–30 cm). The current firmware uses 30 mm (3 cm), which is practically physical contact with a bumper. A recommended configuration profile should allow expanding the solid tone threshold to ~200–300 mm.
2. **Hysteresis (Anti-Flicker Buffer)**:
   - When hovering near a zone boundary (e.g. 400 mm), sensor jitter causes rapid switching between zones (auditory flutter).
   - A hysteresis band of **15 mm to 30 mm** is standard: transition into a closer zone occurs at threshold $D$, but transitioning back out requires reaching $D + \Delta_{hysteresis}$.
3. **Outlier Filtering & Debouncing**:
   - Ultrasonic / ToF acoustic signals can experience acoustic multipath bounce or occasional miss readings (`0` or out-of-range).
   - Recommended: A 3-to-5 sample sliding median filter or low-pass exponential moving average (EMA) to prevent single spurious packet beep glitches.
4. **Failsafe & Stale Data Policy**:
   - If BLE notifications cease for $> 500\text{ ms}$, the system must declare `SENSOR_OFFLINE` / `STALE` and suppress active alerts, alerting the driver visually rather than relying on stale distance metrics.

---

## 3. Data & Storage Considerations (OLAP Cube / VPS Ingestion)
- **Local Storage**: JSON Lines (`.jsonl`) or lightweight SQLite database on Raspberry Pi.
- **Future VPS & Specialized Cube Data Model**:
  - Fact Table: `fact_parking_events` (event_id, session_id, timestamp, min_distance_mm, duration_sec, alert_count, max_zone).
  - Dimension Tables: `dim_device` (device_id, firmware_ver, calibration_profile), `dim_time` (date, time_of_day, day_of_week).
  - Cube Measures: Average approach speed, minimum clearance distribution, false positive rates, session frequencies.

---

## 4. Automotive Resiliency & Fault Tolerance

### A. Automatic BLE Reconnect Loop with Exponential Backoff
- **Current State**: If Bluetooth connectivity drops (e.g., vehicle ignition cycle, alternator voltage sag, or momentary 2.4 GHz RF interference), the watchdog in `reverse_cam_runner.py` properly marks telemetry as `DISCONNECTED` / `STALE`, but the runner does not attempt an active background reconnect. The user or systemd must restart the service.
- **Root Cause & Vulnerability**: Automotive power rails drop during cranking (engine start), momentarily cutting power to accessory-wired ESP32 boards. An in-cabin runner that doesn't actively retry will remain disconnected indefinitely.
- **Recommended Best Practice**:
  - Implement an asynchronous background reconnect task in `reverse_cam_runner.py` / `tools/ble_manager.py` triggered immediately when Bleak detects client disconnect.
  - Apply truncated exponential backoff with jitter:
    - Attempt 1: 1.0s delay
    - Attempt 2: 2.0s delay
    - Attempt 3: 4.0s delay
    - Attempt 4: 8.0s delay
    - Max cap: 30.0s delay (with $\pm 20\%$ jitter to prevent resonance during repeated ignition attempts).
  - During reconnection attempts, keep the Terminal HUD responsive, indicating `RECONNECTING...` in the status gauge.
  - Automatically re-subscribe to `DISTANCE_CHAR_UUID` notifications and restore calibration sync upon reconnect.

---

## 5. Cloud / VPS Telemetry Synchronization

### A. Store-and-Forward Telemetry Architecture
- **Opportunity & Current Gap**: `.env.example` defines `SERVER_LOG_API_URL` and `SERVER_API_KEY`, but `tools/session_logger.py` only writes records locally with `"sync_status": "LOCAL_STORED"`.
- **Automotive Network Realities**: Vehicles frequently operate in garages, underground basements, or cellular dead zones where internet is unavailable. Direct real-time streaming to a cloud API leads to lost records or thread blocking.
- **Recommended Best Practice**:
  - Implement an offline-first **Store-and-Forward** architecture:
    1. Write every completed parking session immediately to local disk (`data/parking_sessions.jsonl`) with `"sync_status": "LOCAL_STORED"`.
    2. Add a `sync_pending_sessions()` worker method that triggers when connectivity is available (e.g., home Wi-Fi connect or LTE link up).
    3. Use standard Python `urllib.request` (zero external dependencies) or `requests` with a strict connection timeout (2.0s).
    4. Upon successful HTTP 200/201 response from `SERVER_LOG_API_URL`, update record status in-place to `"sync_status": "VPS_SYNCED"` with a `synced_at` ISO timestamp.
  - Adhere strictly to the star-schema `ParkingSessionFact` defined in `gemini.md` (Schema C) to populate analytical cubes directly in ClickHouse / PostgreSQL / BigQuery.
