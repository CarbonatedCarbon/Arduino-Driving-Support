#!/usr/bin/env python3
"""
Layer 3 Tool: Proximity Signal Filter & Hysteresis State Machine
===============================================================
Implements ISO 17386 compliant 3-sample median filter,
hysteresis zone banding, and stale data failsafe guard.
Conforms to Schema B in gemini.md.
"""

import time
from datetime import datetime, timezone
from typing import Dict, Any, List


class ProximityFilter:
    def __init__(
        self,
        max_warning_mm: int = 800,
        mid_zone_mm: int = 400,
        close_zone_mm: int = 150,
        solid_tone_mm: int = 30,
        hysteresis_mm: int = 20,
        watchdog_timeout_sec: float = 0.5,
    ):
        self.max_warning_mm = max_warning_mm
        self.mid_zone_mm = mid_zone_mm
        self.close_zone_mm = close_zone_mm
        self.solid_tone_mm = solid_tone_mm
        self.hysteresis_mm = hysteresis_mm
        self.watchdog_timeout_sec = watchdog_timeout_sec

        self.buzzer_volume_pct: int = 8
        self._history: List[int] = []
        self._window_size = 3
        self._current_zone = "SAFE_CLEAR"
        self._last_reading_time: float = 0.0

    def update_settings(self, settings_list: List[int]):
        """Update thresholds from 8-parameter CSV list."""
        if len(settings_list) >= 8:
            self.max_warning_mm = settings_list[0]
            self.mid_zone_mm = settings_list[1]
            self.close_zone_mm = settings_list[2]
            self.solid_tone_mm = settings_list[3]
            self.buzzer_volume_pct = settings_list[7]

    def process_reading(self, raw_distance_mm: int) -> Dict[str, Any]:
        """
        Process a new raw sensor reading.
        Applies median filter, updates hysteresis zone, and generates telemetry record.
        """
        now = time.time()
        self._last_reading_time = now

        # Reject negative or out-of-range sensor noise
        if raw_distance_mm <= 0:
            filtered_distance = 0
            self._current_zone = "SAFE_CLEAR"
        else:
            # 3-sample median filter
            self._history.append(raw_distance_mm)
            if len(self._history) > self._window_size:
                self._history.pop(0)

            sorted_window = sorted(self._history)
            filtered_distance = sorted_window[len(sorted_window) // 2]
            self._current_zone = self._calculate_zone_with_hysteresis(filtered_distance)

        buzzer_active = self._current_zone in ("FAR_ZONE", "MID_ZONE", "CLOSE_ZONE", "DANGER_SOLID")

        return {
            "timestamp_iso": datetime.now(timezone.utc).isoformat(),
            "raw_distance_mm": raw_distance_mm,
            "filtered_distance_mm": filtered_distance,
            "zone": self._current_zone,
            "buzzer_active": buzzer_active,
            "buzzer_volume_pct": self.buzzer_volume_pct if buzzer_active else 0,
            "signal_status": "HEALTHY",
        }

    def check_watchdog(self) -> Dict[str, Any]:
        """
        Evaluate watchdog timer for stale readings.
        If no reading received for > watchdog_timeout_sec, triggers failsafe.
        """
        now = time.time()
        time_since_last = now - self._last_reading_time if self._last_reading_time > 0 else 999.0

        if self._last_reading_time > 0 and time_since_last > self.watchdog_timeout_sec:
            self._current_zone = "DISCONNECTED"
            return {
                "timestamp_iso": datetime.now(timezone.utc).isoformat(),
                "raw_distance_mm": 0,
                "filtered_distance_mm": 0,
                "zone": "DISCONNECTED",
                "buzzer_active": False,
                "buzzer_volume_pct": 0,
                "signal_status": "STALE",
            }
        return {}

    def _calculate_zone_with_hysteresis(self, distance: int) -> str:
        """
        Determine zone with hysteresis deadband:
        Entering closer zone: dist <= threshold
        Exiting to farther zone: dist > threshold + hysteresis
        """
        h = self.hysteresis_mm

        # If currently in DANGER_SOLID
        if self._current_zone == "DANGER_SOLID":
            if distance > (self.solid_tone_mm + h):
                # Fall back to CLOSE_ZONE
                return self._check_close_or_higher(distance)
            return "DANGER_SOLID"

        # If currently in CLOSE_ZONE
        elif self._current_zone == "CLOSE_ZONE":
            if distance <= self.solid_tone_mm:
                return "DANGER_SOLID"
            elif distance > (self.close_zone_mm + h):
                return self._check_mid_or_higher(distance)
            return "CLOSE_ZONE"

        # If currently in MID_ZONE
        elif self._current_zone == "MID_ZONE":
            if distance <= self.solid_tone_mm:
                return "DANGER_SOLID"
            elif distance <= self.close_zone_mm:
                return "CLOSE_ZONE"
            elif distance > (self.mid_zone_mm + h):
                return self._check_far_or_higher(distance)
            return "MID_ZONE"

        # If currently in FAR_ZONE
        elif self._current_zone == "FAR_ZONE":
            if distance <= self.solid_tone_mm:
                return "DANGER_SOLID"
            elif distance <= self.close_zone_mm:
                return "CLOSE_ZONE"
            elif distance <= self.mid_zone_mm:
                return "MID_ZONE"
            elif distance > (self.max_warning_mm + h):
                return "SAFE_CLEAR"
            return "FAR_ZONE"

        # Default / SAFE_CLEAR
        else:
            if distance <= self.solid_tone_mm:
                return "DANGER_SOLID"
            elif distance <= self.close_zone_mm:
                return "CLOSE_ZONE"
            elif distance <= self.mid_zone_mm:
                return "MID_ZONE"
            elif distance <= self.max_warning_mm:
                return "FAR_ZONE"
            return "SAFE_CLEAR"

    def _check_close_or_higher(self, dist: int) -> str:
        if dist <= self.close_zone_mm:
            return "CLOSE_ZONE"
        return self._check_mid_or_higher(dist)

    def _check_mid_or_higher(self, dist: int) -> str:
        if dist <= self.mid_zone_mm:
            return "MID_ZONE"
        return self._check_far_or_higher(dist)

    def _check_far_or_higher(self, dist: int) -> str:
        if dist <= self.max_warning_mm:
            return "FAR_ZONE"
        return "SAFE_CLEAR"
