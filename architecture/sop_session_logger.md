# SOP: Parking Session & Analytical Cube Logging

## 1. Goal
Log real-time telemetry locally and compute session-level analytical fact records conforming to the `ParkingSessionFact` star-schema data model for future VPS ingestion.

## 2. Storage Architecture
- **Raw Stream Buffer**: `.tmp/session_telemetry.jsonl` (ephemeral intermediate log for active sessions).
- **Persistent Facts Archive**: `data/parking_sessions.jsonl` (local permanent analytical store).

## 3. Operational Logic
1. **Session Lifecycle**:
   - A parking session begins when proximity enters `FAR_ZONE` or closer ($< 800\text{ mm}$).
   - Session continues while reversing/maneuvering.
   - Session concludes when distance remains `SAFE_CLEAR` ($> 800\text{ mm}$) for $> 5\text{ seconds}$ or when the application is stopped.
2. **Fact Aggregation (`ParkingSessionFact`)**:
   - `session_id`: Unique UUIDv4.
   - `device_id`: Configured identifier (e.g. `esp32_cam_rev_01`).
   - `start_time_iso` / `end_time_iso`.
   - `duration_seconds`: Total active session duration.
   - `min_distance_mm`: Minimum clearance recorded during the maneuver.
   - `max_alert_zone`: Highest severity zone reached (`FAR_ZONE`, `MID_ZONE`, `CLOSE_ZONE`, or `DANGER_SOLID`).
   - `solid_tone_triggers`: Number of distinct transitions into `DANGER_SOLID`.
   - `readings_count`: Total valid sensor samples processed.
   - `avg_approach_speed_mm_s`: Estimated approach rate $(\Delta d / \Delta t)$.
   - `sync_status`: Flagged as `LOCAL_STORED` (ready for VPS sync).

## 4. Edge Cases
- Session interrupted by disconnection: fact is closed and saved with whatever data was accumulated.
- Disk write failure: log error to stderr, do not crash main process.
