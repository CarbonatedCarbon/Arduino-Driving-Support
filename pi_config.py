#!/usr/bin/env python3
"""
ReverseCam BLE Configuration Tool
==================================
Connects to the ESP32 parking sensor via Bluetooth Low Energy
to configure distance thresholds and beep intervals in real-time.

Usage:
    pip install bleak
    python3 pi_config.py

Requires: Python 3.7+, bleak
"""

import asyncio
import sys
from bleak import BleakClient, BleakScanner

# ==========================================
# BLE UUIDs — must match the ESP32 firmware
# ==========================================
SERVICE_UUID       = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
SETTINGS_CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
DISTANCE_CHAR_UUID = "1c95d5e3-d8f7-413a-bf3d-7a2e5d7be87e"

DEVICE_NAME = "ReverseCam"

# ==========================================
# Setting definitions
# ==========================================
SETTING_NAMES = [
    "Max Warning Distance  (mm)",
    "Mid Zone Distance     (mm)",
    "Close Zone Distance   (mm)",
    "Solid Tone Distance   (mm)",
    "Far Zone Beep Interval(ms)",
    "Mid Zone Beep Interval(ms)",
    "Close Zone Beep Intrvl(ms)",
    "Buzzer Volume        (0-100%)",
]

DEFAULTS = [800, 400, 150, 30, 600, 300, 100, 8]


# ==========================================
# BLE Operations
# ==========================================
async def find_device():
    """Scan for the ReverseCam ESP32 over BLE."""
    print(f"\n  Scanning for '{DEVICE_NAME}'...")
    devices = await BleakScanner.discover(timeout=5.0)
    for device in devices:
        if device.name and DEVICE_NAME in device.name:
            print(f"  Found: {device.name} ({device.address})")
            return device.address
    return None


async def read_settings(client):
    """Read the current settings CSV from the ESP32 and return as a list of ints."""
    data = await client.read_gatt_char(SETTINGS_CHAR_UUID)
    csv_str = data.decode("utf-8")
    return [int(v) for v in csv_str.split(",")]


async def write_settings(client, values):
    """Write settings to the ESP32 as a CSV string."""
    csv_str = ",".join(str(v) for v in values)
    await client.write_gatt_char(SETTINGS_CHAR_UUID, csv_str.encode("utf-8"), response=True)


# ==========================================
# Display Helpers
# ==========================================
def display_banner():
    print()
    print("  ============================================")
    print("    ReverseCam  —  BLE Configuration Tool")
    print("  ============================================")


def display_settings(values):
    print()
    print("  +----+-------------------------------+-------+")
    print("  | #  | Setting                       | Value |")
    print("  +----+-------------------------------+-------+")
    for i, (name, val) in enumerate(zip(SETTING_NAMES, values)):
        print(f"  | {i+1}  | {name} | {val:>5} |")
    print("  +----+-------------------------------+-------+")


def display_menu():
    print()
    print("  Options:")
    print(f"    [1-{len(SETTING_NAMES)}]  Change a setting")
    print("    [a]    Change all settings at once")
    print("    [m]    Monitor live distance")
    print("    [r]    Reset to defaults")
    print("    [q]    Quit")


# ==========================================
# Live Distance Monitor
# ==========================================
async def monitor_distance(client):
    """Subscribe to BLE notifications for real-time distance readings."""
    print()
    print("  Live Distance Monitor  (press Ctrl+C to stop)")
    print("  " + "-" * 42)

    def on_notify(sender, data):
        try:
            dist = data.decode("utf-8")
            bar_len = min(int(int(dist) / 20), 40)  # Scale: 800mm = 40 chars
            bar = "#" * bar_len
            print(f"\r  Distance: {dist:>5} mm  |{bar:<40}|", end="", flush=True)
        except ValueError:
            pass

    await client.start_notify(DISTANCE_CHAR_UUID, on_notify)
    try:
        while True:
            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        await client.stop_notify(DISTANCE_CHAR_UUID)
        print()
        print("  Monitoring stopped.")


# ==========================================
# Interactive Menu
# ==========================================
async def interactive_menu(client):
    """Main interactive configuration loop."""
    while True:
        try:
            settings = await read_settings(client)
        except Exception as e:
            print(f"\n  Error reading settings: {e}")
            break

        display_settings(settings)
        display_menu()

        try:
            choice = input("\n  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            choice = "q"

        if choice == "q":
            print("\n  Disconnecting...")
            break

        elif choice == "m":
            await monitor_distance(client)

        elif choice == "r":
            try:
                await write_settings(client, DEFAULTS)
                print("  Reset to defaults.")
            except Exception as e:
                print(f"  Error: {e}")

        elif choice == "a":
            print()
            print(f"  Enter all {len(SETTING_NAMES)} values separated by commas:")
            print("  Format: " + ",".join(n.split()[0].lower() for n in SETTING_NAMES))
            raw = input("  > ").strip()
            try:
                new_values = [int(v.strip()) for v in raw.split(",")]
                if len(new_values) != len(SETTING_NAMES):
                    print(f"  Error: exactly {len(SETTING_NAMES)} values required.")
                    continue
                await write_settings(client, new_values)
                print("  All settings updated.")
            except ValueError:
                print("  Error: all values must be integers.")
            except Exception as e:
                print(f"  Error: {e}")

        elif choice.isdigit() and 1 <= int(choice) <= len(SETTING_NAMES):
            idx = int(choice) - 1
            current = settings[idx]
            raw = input(f"  New value for '{SETTING_NAMES[idx].strip()}' (current: {current}): ").strip()
            try:
                new_val = int(raw)
                settings[idx] = new_val
                await write_settings(client, settings)
                print(f"  Updated: {SETTING_NAMES[idx].strip()} = {new_val}")
            except ValueError:
                print("  Error: value must be an integer.")
            except Exception as e:
                print(f"  Error: {e}")

        else:
            print("  Invalid option.")


# ==========================================
# Main
# ==========================================
async def main():
    display_banner()

    address = await find_device()
    if not address:
        print("  Device not found. Make sure the ESP32 is powered on and nearby.")
        print("  Tip: check that Bluetooth is enabled on this Pi.")
        return

    print(f"\n  Connecting to {address}...")

    try:
        async with BleakClient(address) as client:
            if client.is_connected:
                print("  Connected!")
                await interactive_menu(client)
            else:
                print("  Failed to connect.")
    except Exception as e:
        print(f"  Connection error: {e}")
        print("  Make sure the ESP32 is powered on and in range.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n  Goodbye.")
        sys.exit(0)
