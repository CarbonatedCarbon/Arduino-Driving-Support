# Project Constitution (`gemini.md`)

> **B.L.A.S.T. & A.N.T. Invariant Notice:**  
> This file is law. The planning files are memory.  
> Update this file ONLY when a schema changes, a rule is added, or architecture is modified.

---

## 1. Architectural Invariants (A.N.T.)
- **Layer 1: Architecture (`architecture/`)**  
  Technical SOPs written in Markdown. Must define goals, inputs, outputs, error handling, and tool logic. If logic changes, update the SOP before updating code.
- **Layer 2: Navigation (Decision Making)**  
  Agent reasoning layer routing data between SOPs and Layer 3 Tools.
- **Layer 3: Tools (`tools/`)**  
  Deterministic, single-purpose, atomic, testable Python scripts. Secrets loaded from `.env`. Intermediate files strictly stored in `.tmp/`.
- **System Boundaries**:
  - Direct hardware communication is BLE only via bleak.
  - Configuration UUIDs loaded strictly from `.env`.
  - Local storage on Pi uses append-only JSON Lines / SQLite. Future VPS sync adheres to the analytical fact/dimension cube schema.
  - Failures trigger Self-Annealing (Analyze -> Patch -> Test -> Update Architecture SOP).

---

## 2. Behavioral Rules (Automotive Proximity Standards: ISO 17386 / MALSO)
1. **Hysteresis Banding (Anti-Flicker)**:
   - To eliminate audible chatter when an obstacle hovers near a zone boundary, a hysteresis buffer of $\pm 20\text{ mm}$ is enforced. Entering a closer zone occurs at distance $D$; exiting back to a farther zone requires $D + 20\text{ mm}$.
2. **Sensor Spike Filtering**:
   - Raw distance readings from the I2C sensor/BLE notification pass through a 3-sample median filter before updating zone alerts or UI display.
3. **Failsafe & Stale Data Guard**:
   - If no BLE distance notification is received within **500 ms**, the system transitions to state `SENSOR_DISCONNECTED`. Audible alerts are immediately silenced and the UI visually indicates sensor offline to prevent unsafe reversing on stale data.
4. **Hardware Switch & Zero-Reading Handling**:
   - Distance `<= 0` indicates sensor blind-spot or out-of-range (> Max Warning). If the future rocker switch disengages the sensor, the buzzer remains muted (`0%` duty cycle) and UI reflects `STANDBY`.
5. **Deterministic Configuration**:
   - All settings updates written to the ESP32 must conform strictly to the 8-integer CSV schema and must be read back to verify synchronization.
6. **Cross-Platform Terminal Compatibility**:
   - Terminal visualizers must configure `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` to avoid CP1252 encoding crashes on Windows and utilize safe boundary characters.

---

## 3. Data Schemas (JSON)

### Schema A: `ReverseCamSettings` (ESP32 GATT Settings Characteristic)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ReverseCamSettings",
  "type": "object",
  "properties": {
    "distance_max_warning_mm": { "type": "integer", "minimum": 100, "maximum": 2000, "default": 800 },
    "distance_mid_zone_mm":    { "type": "integer", "minimum": 50,  "maximum": 1500, "default": 400 },
    "distance_close_zone_mm":  { "type": "integer", "minimum": 30,  "maximum": 800,  "default": 150 },
    "distance_solid_tone_mm":  { "type": "integer", "minimum": 10,  "maximum": 500,  "default": 30 },
    "beep_interval_far_ms":    { "type": "integer", "minimum": 50,  "maximum": 2000, "default": 600 },
    "beep_interval_mid_ms":    { "type": "integer", "minimum": 30,  "maximum": 1500, "default": 300 },
    "beep_interval_close_ms":  { "type": "integer", "minimum": 10,  "maximum": 500,  "default": 100 },
    "buzzer_volume_pct":       { "type": "integer", "minimum": 0,   "maximum": 100,  "default": 8 }
  },
  "required": [
    "distance_max_warning_mm",
    "distance_mid_zone_mm",
    "distance_close_zone_mm",
    "distance_solid_tone_mm",
    "beep_interval_far_ms",
    "beep_interval_mid_ms",
    "beep_interval_close_ms",
    "buzzer_volume_pct"
  ]
}
```

### Schema B: `ReverseCamTelemetry` (Real-Time Sensor Telemetry)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ReverseCamTelemetry",
  "type": "object",
  "properties": {
    "timestamp_iso": { "type": "string", "format": "date-time" },
    "raw_distance_mm": { "type": "integer" },
    "filtered_distance_mm": { "type": "integer" },
    "zone": { 
      "type": "string", 
      "enum": ["SAFE_CLEAR", "FAR_ZONE", "MID_ZONE", "CLOSE_ZONE", "DANGER_SOLID", "DISCONNECTED"] 
    },
    "buzzer_active": { "type": "boolean" },
    "buzzer_volume_pct": { "type": "integer", "minimum": 0, "maximum": 100 },
    "signal_status": { "type": "string", "enum": ["HEALTHY", "STALE", "DISCONNECTED"] }
  },
  "required": [
    "timestamp_iso",
    "raw_distance_mm",
    "filtered_distance_mm",
    "zone",
    "buzzer_active",
    "buzzer_volume_pct",
    "signal_status"
  ]
}
```

### Schema C: `ParkingSessionFact` (Cube Data Model / VPS Analytical Storage)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ParkingSessionFact",
  "description": "Star-schema fact record for parking telemetry aggregation",
  "type": "object",
  "properties": {
    "session_id": { "type": "string", "format": "uuid" },
    "device_id": { "type": "string", "default": "esp32_cam_rev_01" },
    "start_time_iso": { "type": "string", "format": "date-time" },
    "end_time_iso": { "type": "string", "format": "date-time" },
    "duration_seconds": { "type": "number", "minimum": 0 },
    "min_distance_mm": { "type": "integer" },
    "max_alert_zone": { 
      "type": "string", 
      "enum": ["SAFE_CLEAR", "FAR_ZONE", "MID_ZONE", "CLOSE_ZONE", "DANGER_SOLID"] 
    },
    "solid_tone_triggers": { "type": "integer", "minimum": 0 },
    "readings_count": { "type": "integer", "minimum": 1 },
    "avg_approach_speed_mm_s": { "type": "number" },
    "sync_status": { "type": "string", "enum": ["LOCAL_STORED", "VPS_SYNCED", "SYNC_PENDING"] }
  },
  "required": [
    "session_id",
    "device_id",
    "start_time_iso",
    "end_time_iso",
    "duration_seconds",
    "min_distance_mm",
    "max_alert_zone",
    "solid_tone_triggers",
    "readings_count",
    "sync_status"
  ]
}
```

---

## 4. Maintenance Log
- **2026-10-01**: Constitution initialized under B.L.A.S.T. Protocol 0.
- **2026-10-01**: Processed Phase 1 Discovery answers (BLE only, `.env` UUID configuration, ISO 17386 proximity research, Cube Data Model schema).
- **2026-10-01**: Phase 2 Link verified. Handshake tool `tools/ble_link_test.py` validated host adapter and `.env` loader.
- **2026-10-01**: Phase 3 Architecture established. Layer 1 SOPs created, Layer 3 tools built (`tools/proximity_filter.py`, `tools/session_logger.py`, `tools/ble_manager.py`, `tools/terminal_hud.py`). Self-annealing executed to patch Windows CP1252 stdout encoding.
- **2026-10-01**: Phase 4 Stylize completed. Terminal HUD validated with real-time ANSI gauge and zone alerts.
- **2026-10-01**: Phase 5 Trigger deployed. Raspberry Pi systemd service created in `deploy/reverse-cam.service` and automated setup in `deploy/setup_pi.sh`.
- **2026-10-05**: Codebase hardening: Implemented ESP32 Preferences flash storage persistence in `reverse_cam.ino`, dynamic `.env` configuration in `pi_config.py`, and separated test suite into dedicated `tests/` with `conftest.py`. Defined Phase 6 roadmap for BLE Auto-Reconnect with Exponential Backoff and Store-and-Forward VPS Sync.
