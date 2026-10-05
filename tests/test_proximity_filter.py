#!/usr/bin/env python3
"""
Unit Tests for ProximityFilter (Layer 3 Verification)
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.proximity_filter import ProximityFilter


def test_median_filter():
    pf = ProximityFilter()
    # Feed 3 values: 450, 999 (glitch spike), 460 -> median should be 460
    pf.process_reading(450)
    pf.process_reading(999)
    res = pf.process_reading(460)
    assert res["filtered_distance_mm"] == 460, f"Expected 460, got {res['filtered_distance_mm']}"
    print("[PASS] test_median_filter")


def test_hysteresis_boundary():
    pf = ProximityFilter(
        max_warning_mm=800,
        mid_zone_mm=400,
        close_zone_mm=150,
        solid_tone_mm=30,
        hysteresis_mm=20,
    )
    # Start at 500mm -> FAR_ZONE
    for _ in range(3):
        res = pf.process_reading(500)
    assert res["zone"] == "FAR_ZONE"

    # Cross into MID_ZONE at exactly 400mm
    for _ in range(3):
        res = pf.process_reading(400)
    assert res["zone"] == "MID_ZONE", f"Expected MID_ZONE, got {res['zone']}"

    # Move back out to 415mm (within the 20mm hysteresis band 400..420)
    # Should STILL remain in MID_ZONE!
    for _ in range(3):
        res = pf.process_reading(415)
    assert res["zone"] == "MID_ZONE", f"Hysteresis failed! Expected MID_ZONE at 415mm, got {res['zone']}"

    # Move beyond hysteresis band to 425mm -> should switch back to FAR_ZONE
    for _ in range(3):
        res = pf.process_reading(425)
    assert res["zone"] == "FAR_ZONE", f"Expected FAR_ZONE at 425mm, got {res['zone']}"

    print("[PASS] test_hysteresis_boundary")


def test_danger_solid_zone():
    pf = ProximityFilter(solid_tone_mm=30, hysteresis_mm=20)
    for _ in range(3):
        res = pf.process_reading(25)
    assert res["zone"] == "DANGER_SOLID"
    assert res["buzzer_active"] is True

    # Moving to 40mm (within 30 + 20 = 50mm) stays in DANGER_SOLID
    for _ in range(3):
        res = pf.process_reading(40)
    assert res["zone"] == "DANGER_SOLID"

    # Moving to 55mm exits DANGER_SOLID to CLOSE_ZONE
    for _ in range(3):
        res = pf.process_reading(55)
    assert res["zone"] == "CLOSE_ZONE"

    print("[PASS] test_danger_solid_zone")


def test_stale_watchdog():
    pf = ProximityFilter(watchdog_timeout_sec=0.1)
    pf.process_reading(300)
    time.sleep(0.15)
    stale_res = pf.check_watchdog()
    assert stale_res.get("zone") == "DISCONNECTED"
    assert stale_res.get("signal_status") == "STALE"
    print("[PASS] test_stale_watchdog")


if __name__ == "__main__":
    test_median_filter()
    test_hysteresis_boundary()
    test_danger_solid_zone()
    test_stale_watchdog()
    print("All proximity filter unit tests passed successfully!")
