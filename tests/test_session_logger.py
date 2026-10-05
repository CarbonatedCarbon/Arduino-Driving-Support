#!/usr/bin/env python3
"""
Unit Tests for ParkingSessionLogger (Layer 3 Verification)
=========================================================
Tests session initialization, telemetry aggregation, and fact record persistence.
Conforms to standard pytest naming and discovery conventions.
"""

import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.session_logger import ParkingSessionLogger


def test_session_lifecycle(tmp_path=None):
    """Verify end-to-end session aggregation from warning zone entry to finalization."""
    stream_path = (tmp_path / "test_telemetry.jsonl") if tmp_path else None
    fact_path = (tmp_path / "test_sessions.jsonl") if tmp_path else None

    logger = ParkingSessionLogger(
        device_id="test_unit_01",
        stream_log_path=stream_path,
        fact_store_path=fact_path,
    )

    # Initial state
    assert logger.current_session_id is None

    # Safe clear reading should not start session
    logger.log_telemetry({"zone": "SAFE_CLEAR", "filtered_distance_mm": 950})
    assert logger.current_session_id is None

    # Entering FAR_ZONE starts session
    logger.log_telemetry({"zone": "FAR_ZONE", "filtered_distance_mm": 600})
    assert logger.current_session_id is not None
    sess_id = logger.current_session_id

    # Approach obstacle through zones
    logger.log_telemetry({"zone": "MID_ZONE", "filtered_distance_mm": 350})
    logger.log_telemetry({"zone": "CLOSE_ZONE", "filtered_distance_mm": 120})
    logger.log_telemetry({"zone": "DANGER_SOLID", "filtered_distance_mm": 25})
    logger.log_telemetry({"zone": "DANGER_SOLID", "filtered_distance_mm": 20})

    # Finalize session
    fact = logger.finalize_session()
    assert fact is not None
    assert fact["session_id"] == sess_id
    assert fact["min_distance_mm"] == 20
    assert fact["max_alert_zone"] == "DANGER_SOLID"
    assert fact["solid_tone_triggers"] == 1
    assert fact["readings_count"] == 5
    assert fact["sync_status"] == "LOCAL_STORED"


def test_session_finalize_without_readings(tmp_path=None):
    """Verify finalize_session returns None when no active session has occurred."""
    logger = ParkingSessionLogger(
        device_id="test_unit_02",
        stream_log_path=(tmp_path / "empty_stream.jsonl") if tmp_path else None,
        fact_store_path=(tmp_path / "empty_facts.jsonl") if tmp_path else None,
    )
    fact = logger.finalize_session()
    assert fact is None


if __name__ == "__main__":
    test_session_lifecycle()
    test_session_finalize_without_readings()
    print("All session logger unit tests passed successfully!")
