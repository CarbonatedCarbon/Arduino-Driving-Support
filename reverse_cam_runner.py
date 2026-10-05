#!/usr/bin/env python3
"""
ReverseCam Orchestration Runner (Layer 2 Navigation)
====================================================
Wires together:
- tools/ble_manager.py     (BLE Connection & GATT interface)
- tools/proximity_filter.py (Median filter & Hysteresis state machine)
- tools/session_logger.py  (Analytical cube data model logger)
- tools/terminal_hud.py    (Real-time terminal visualizer)

Usage:
    python reverse_cam_runner.py [--simulate] [--timeout SECONDS] [--demo-frames N]
"""

import sys
import os
import time
import argparse
import asyncio
from pathlib import Path

# Ensure root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tools.ble_manager import BLEManager
from tools.proximity_filter import ProximityFilter
from tools.session_logger import ParkingSessionLogger
from tools.terminal_hud import TerminalHUD


async def main():
    parser = argparse.ArgumentParser(description="ReverseCam Parking Support System")
    parser.add_argument("--simulate", action="store_true", help="Run with simulated trajectory")
    parser.add_argument("--timeout", type=float, default=5.0, help="BLE discovery timeout (seconds)")
    parser.add_argument("--demo-frames", type=int, default=0, help="Exit after N frames (for automated testing)")
    args = parser.parse_args()

    # Initialize components
    ble_mgr = BLEManager(simulate=args.simulate)
    filter_engine = ProximityFilter()
    session_logger = ParkingSessionLogger(device_id=os.getenv("SERVER_DEVICE_ID", "esp32_cam_rev_01"))
    hud = TerminalHUD()

    print("[*] Starting ReverseCam System...")
    connected = await ble_mgr.scan_and_connect(timeout_sec=args.timeout)

    if not connected and not args.simulate:
        print("[!] Could not connect to ReverseCam over BLE.")
        print("    Tip: Use 'python reverse_cam_runner.py --simulate' to test without physical hardware.")
        sys.exit(1)

    # Sync settings with filter engine
    settings = await ble_mgr.read_settings()
    filter_engine.update_settings(settings)

    latest_telemetry = {
        "timestamp_iso": "",
        "raw_distance_mm": 0,
        "filtered_distance_mm": 0,
        "zone": "SAFE_CLEAR",
        "buzzer_active": False,
        "buzzer_volume_pct": filter_engine.buzzer_volume_pct,
        "signal_status": "WAITING_DATA",
    }

    def on_distance_received(raw_dist: int):
        nonlocal latest_telemetry
        telemetry = filter_engine.process_reading(raw_dist)
        session_logger.log_telemetry(telemetry)
        latest_telemetry = telemetry

    await ble_mgr.start_distance_stream(on_distance_received)
    hud.clear_screen()

    frame_count = 0
    try:
        while True:
            # 1. Check watchdog for stale data (>500ms)
            stale_status = filter_engine.check_watchdog()
            if stale_status:
                latest_telemetry = stale_status
                session_logger.log_telemetry(latest_telemetry)

            # 2. Extract active session metrics
            session_info = {
                "min_distance_mm": session_logger.min_distance_mm,
                "solid_tone_triggers": session_logger.solid_tone_triggers,
                "readings_count": session_logger.readings_count,
            }

            # 3. Render HUD
            hud.render(
                latest_telemetry,
                session_info=session_info,
                is_simulated=args.simulate,
            )

            frame_count += 1
            if args.demo_frames > 0 and frame_count >= args.demo_frames:
                break

            await asyncio.sleep(0.08)  # ~12.5 Hz refresh

    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        print("\n\n[*] Shutting down...")
        await ble_mgr.stop_distance_stream()
        await ble_mgr.disconnect()

        # Finalize and persist session fact
        fact = session_logger.finalize_session()
        if fact:
            print(f"[+] Saved parking session fact to data/parking_sessions.jsonl:")
            print(f"    Session ID: {fact['session_id']}")
            print(f"    Min Distance: {fact['min_distance_mm']} mm | Solid Tones: {fact['solid_tone_triggers']}")
            print(f"    Max Alert Zone: {fact['max_alert_zone']} | Duration: {fact['duration_seconds']}s")
        else:
            print("[*] No active parking session needed finalization.")
        print("[+] Done.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
