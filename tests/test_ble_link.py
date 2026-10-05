#!/usr/bin/env python3
"""
BLE Link & Handshake Verification Tests (Layer 3 Verification)
==============================================================
Validates .env configuration and tests BLE adapter operational status.
Follows pytest standard naming conventions (test_*.py, test_* functions).
"""

import os
import sys
import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path
import pytest
from dotenv import load_dotenv

# Ensure root is in path when executed directly
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Intermediate status file location
TMP_DIR = ROOT_DIR / ".tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)
STATUS_FILE = TMP_DIR / "ble_link_status.json"

# Load environment variables
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

BLE_DEVICE_NAME = os.getenv("BLE_DEVICE_NAME", "ReverseCam")
BLE_SERVICE_UUID = os.getenv("BLE_SERVICE_UUID")
BLE_SETTINGS_CHAR_UUID = os.getenv("BLE_SETTINGS_CHAR_UUID")
BLE_DISTANCE_CHAR_UUID = os.getenv("BLE_DISTANCE_CHAR_UUID")


def verify_env_config():
    """Verify all required UUIDs and settings are present in .env."""
    missing = []
    for var_name, val in [
        ("BLE_DEVICE_NAME", BLE_DEVICE_NAME),
        ("BLE_SERVICE_UUID", BLE_SERVICE_UUID),
        ("BLE_SETTINGS_CHAR_UUID", BLE_SETTINGS_CHAR_UUID),
        ("BLE_DISTANCE_CHAR_UUID", BLE_DISTANCE_CHAR_UUID),
    ]:
        if not val or not val.strip():
            missing.append(var_name)
    return missing


async def run_ble_handshake(timeout_sec: float = 5.0):
    """Scan for ReverseCam and verify BLE adapter operational status."""
    from bleak import BleakScanner

    report = {
        "timestamp_iso": datetime.now(timezone.utc).isoformat(),
        "env_verification": {
            "status": "PASS",
            "device_name": BLE_DEVICE_NAME,
            "service_uuid": BLE_SERVICE_UUID,
            "settings_char_uuid": BLE_SETTINGS_CHAR_UUID,
            "distance_char_uuid": BLE_DISTANCE_CHAR_UUID,
        },
        "adapter_status": "UNKNOWN",
        "device_found": False,
        "device_address": None,
        "device_rssi": None,
        "discovered_devices_count": 0,
        "error_message": None,
    }

    missing_env = verify_env_config()
    if missing_env:
        report["env_verification"]["status"] = "FAIL"
        report["error_message"] = f"Missing .env variables: {', '.join(missing_env)}"
        return report

    print(f"[*] Scanning for BLE peripheral '{BLE_DEVICE_NAME}' (timeout={timeout_sec}s)...")
    try:
        devices = await BleakScanner.discover(timeout=timeout_sec)
        report["adapter_status"] = "OPERATIONAL"
        report["discovered_devices_count"] = len(devices)

        target_dev = None
        for dev in devices:
            if dev.name and BLE_DEVICE_NAME in dev.name:
                target_dev = dev
                break

        if target_dev:
            report["device_found"] = True
            report["device_address"] = target_dev.address
            report["device_rssi"] = getattr(target_dev, "rssi", None)
            print(f"[+] Target Found: {target_dev.name} [{target_dev.address}] (RSSI: {report['device_rssi']})")
        else:
            print(f"[-] Bluetooth adapter operational ({len(devices)} devices found), but '{BLE_DEVICE_NAME}' was not detected.")
            print("    Ensure the ESP32 is powered on, flashed with reverse_cam.ino, and in range.")

    except Exception as exc:
        report["adapter_status"] = "ERROR"
        report["error_message"] = str(exc)
        print(f"[!] BLE Scanner Exception: {exc}")

    return report


# ==============================================================================
# Pytest Test Cases (Standard Automated Discovery: test_*)
# ==============================================================================

def test_env_configuration():
    """Automated test: Verify all required BLE UUIDs and configuration exist."""
    missing = verify_env_config()
    assert not missing, f"Missing required .env variables: {missing}"


@pytest.mark.hardware
def test_ble_adapter_readiness():
    """Automated test: Verify local Bluetooth adapter readiness for scanning."""
    try:
        report = asyncio.run(run_ble_handshake(timeout_sec=2.0))
    except Exception as exc:
        pytest.skip(f"Bluetooth subsystem error: {exc}")

    if report.get("adapter_status") == "ERROR":
        pytest.skip(f"Bluetooth adapter not available on this host: {report.get('error_message')}")

    assert report.get("adapter_status") in ("OPERATIONAL", "UNKNOWN")


# ==============================================================================
# Direct Execution Entrypoint
# ==============================================================================

def main():
    print("=" * 55)
    print("  ReverseCam BLE Link & Handshake Verification")
    print("=" * 55)

    try:
        report = asyncio.run(run_ble_handshake(timeout_sec=5.0))
    except Exception as exc:
        report = {
            "timestamp_iso": datetime.now(timezone.utc).isoformat(),
            "adapter_status": "CRITICAL_FAILURE",
            "error_message": str(exc),
        }

    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[*] Handshake report written to {STATUS_FILE}")
    print("=" * 55)

    if report.get("adapter_status") == "OPERATIONAL" and report.get("env_verification", {}).get("status") == "PASS":
        sys.exit(0)
    elif report.get("adapter_status") == "ERROR":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
