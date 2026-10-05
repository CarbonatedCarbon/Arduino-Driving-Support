#!/usr/bin/env python3
"""
Layer 3 Tool: Parking Session & Analytical Cube Logger
======================================================
Records real-time telemetry stream to .tmp/session_telemetry.jsonl
and generates aggregated ParkingSessionFact records stored in data/parking_sessions.jsonl.
Conforms to Schema C in gemini.md.
"""

import os
import json
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure directories exist
BASE_DIR = Path(__file__).resolve().parent.parent
TMP_DIR = BASE_DIR / ".tmp"
DATA_DIR = BASE_DIR / "data"
TMP_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

STREAM_LOG = TMP_DIR / "session_telemetry.jsonl"
FACT_STORE = DATA_DIR / "parking_sessions.jsonl"


class ParkingSessionLogger:
    def __init__(
        self,
        device_id: str = "esp32_cam_rev_01",
        stream_log_path: Optional[Path] = None,
        fact_store_path: Optional[Path] = None,
    ):
        self.device_id = device_id
        self.stream_log_path = Path(stream_log_path) if stream_log_path else STREAM_LOG
        self.fact_store_path = Path(fact_store_path) if fact_store_path else FACT_STORE
        self.current_session_id: Optional[str] = None
        self.session_start_time: Optional[float] = None
        self.session_start_iso: Optional[str] = None
        self.readings_count: int = 0
        self.min_distance_mm: int = 9999
        self.max_alert_zone: str = "SAFE_CLEAR"
        self.solid_tone_triggers: int = 0
        self._in_solid_tone: bool = False
        self._last_distance: Optional[int] = None
        self._speed_samples = []

        self._zone_severity = {
            "SAFE_CLEAR": 0,
            "FAR_ZONE": 1,
            "MID_ZONE": 2,
            "CLOSE_ZONE": 3,
            "DANGER_SOLID": 4,
            "DISCONNECTED": -1,
        }

    def log_telemetry(self, telemetry: Dict[str, Any]):
        """Append real-time telemetry to stream log and update session aggregates."""
        # 1. Write to raw stream buffer
        with open(self.stream_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(telemetry) + "\n")

        zone = telemetry.get("zone", "SAFE_CLEAR")
        distance = telemetry.get("filtered_distance_mm", 0)

        # 2. Check session start condition (entering warning zone < 800mm)
        if zone in ("FAR_ZONE", "MID_ZONE", "CLOSE_ZONE", "DANGER_SOLID"):
            if not self.current_session_id:
                self._start_session(telemetry.get("timestamp_iso"))

        if not self.current_session_id:
            return

        # 3. Update session aggregates
        self.readings_count += 1
        if distance > 0 and distance < self.min_distance_mm:
            self.min_distance_mm = distance

        # Update peak zone
        if self._zone_severity.get(zone, 0) > self._zone_severity.get(self.max_alert_zone, 0):
            self.max_alert_zone = zone

        # Track solid tone triggers
        if zone == "DANGER_SOLID":
            if not self._in_solid_tone:
                self.solid_tone_triggers += 1
                self._in_solid_tone = True
        else:
            self._in_solid_tone = False

        # Speed estimation
        if self._last_distance is not None and distance > 0:
            delta_d = abs(self._last_distance - distance)
            self._speed_samples.append(delta_d)
        self._last_distance = distance

    def _start_session(self, timestamp_iso: Optional[str] = None):
        """Initialize a new parking session."""
        self.current_session_id = str(uuid.uuid4())
        self.session_start_time = time.time()
        self.session_start_iso = timestamp_iso or datetime.now(timezone.utc).isoformat()
        self.readings_count = 0
        self.min_distance_mm = 9999
        self.max_alert_zone = "SAFE_CLEAR"
        self.solid_tone_triggers = 0
        self._in_solid_tone = False
        self._speed_samples = []

    def finalize_session(self) -> Optional[Dict[str, Any]]:
        """Close active session, generate fact record, and append to persistent store."""
        if not self.current_session_id or self.readings_count == 0:
            return None

        end_time_iso = datetime.now(timezone.utc).isoformat()
        duration_sec = round(time.time() - (self.session_start_time or time.time()), 2)
        avg_speed = round(sum(self._speed_samples) / len(self._speed_samples), 2) if self._speed_samples else 0.0

        fact_record = {
            "session_id": self.current_session_id,
            "device_id": self.device_id,
            "start_time_iso": self.session_start_iso,
            "end_time_iso": end_time_iso,
            "duration_seconds": max(duration_sec, 0.1),
            "min_distance_mm": self.min_distance_mm if self.min_distance_mm != 9999 else 0,
            "max_alert_zone": self.max_alert_zone,
            "solid_tone_triggers": self.solid_tone_triggers,
            "readings_count": self.readings_count,
            "avg_approach_speed_mm_s": avg_speed,
            "sync_status": "LOCAL_STORED",
        }

        with open(self.fact_store_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(fact_record) + "\n")

        # Reset session
        self.current_session_id = None
        self.session_start_time = None
        return fact_record
