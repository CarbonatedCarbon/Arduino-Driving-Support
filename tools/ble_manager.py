#!/usr/bin/env python3
"""
Layer 3 Tool: BLE Peripheral Client & GATT Manager
===================================================
Manages connection, settings sync, and distance notifications with ESP32.
Loads UUIDs strictly from .env.
Supports simulation mode for offline validation.
"""

import os
import asyncio
from pathlib import Path
from typing import Callable, Optional, List
from dotenv import load_dotenv

# Load .env
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

BLE_DEVICE_NAME = os.getenv("BLE_DEVICE_NAME", "ReverseCam")
BLE_SERVICE_UUID = os.getenv("BLE_SERVICE_UUID")
BLE_SETTINGS_CHAR_UUID = os.getenv("BLE_SETTINGS_CHAR_UUID")
BLE_DISTANCE_CHAR_UUID = os.getenv("BLE_DISTANCE_CHAR_UUID")

DEFAULT_SETTINGS = [800, 400, 150, 30, 600, 300, 100, 8]


class BLEManager:
    def __init__(self, simulate: bool = False):
        self.simulate = simulate
        self.client = None
        self.device_address = None
        self.is_connected = False
        self.notification_callback: Optional[Callable[[int], None]] = None
        self.current_settings: List[int] = list(DEFAULT_SETTINGS)
        self._sim_task: Optional[asyncio.Task] = None
        self._running = False

    async def scan_and_connect(self, timeout_sec: float = 5.0) -> bool:
        """Scan for ReverseCam and establish GATT connection."""
        if self.simulate:
            self.is_connected = True
            print("[SIMULATION] Connected to virtual ReverseCam peripheral.")
            return True

        from bleak import BleakScanner, BleakClient

        print(f"[*] Scanning for '{BLE_DEVICE_NAME}'...")
        devices = await BleakScanner.discover(timeout=timeout_sec)
        for dev in devices:
            if dev.name and BLE_DEVICE_NAME in dev.name:
                self.device_address = dev.address
                print(f"[+] Found {dev.name} at {dev.address}")
                break

        if not self.device_address:
            print(f"[-] '{BLE_DEVICE_NAME}' not found.")
            return False

        print(f"[*] Connecting to {self.device_address}...")
        try:
            self.client = BleakClient(self.device_address)
            await self.client.connect()
            self.is_connected = self.client.is_connected
            if self.is_connected:
                print("[+] BLE Connected successfully.")
                await self.read_settings()
                return True
        except Exception as exc:
            print(f"[!] Connection failed: {exc}")
            self.is_connected = False
        return False

    async def read_settings(self) -> List[int]:
        """Read 8-integer settings CSV from ESP32."""
        if self.simulate:
            return self.current_settings

        if not self.client or not self.client.is_connected:
            return self.current_settings

        try:
            raw = await self.client.read_gatt_char(BLE_SETTINGS_CHAR_UUID)
            csv_str = raw.decode("utf-8").strip()
            self.current_settings = [int(v.strip()) for v in csv_str.split(",")]
            return self.current_settings
        except Exception as exc:
            print(f"[!] Error reading settings: {exc}")
            return self.current_settings

    async def write_settings(self, settings_list: List[int]) -> bool:
        """Write 8-integer settings CSV to ESP32."""
        if len(settings_list) != 8:
            raise ValueError(f"Expected 8 parameters, received {len(settings_list)}")

        self.current_settings = list(settings_list)
        if self.simulate:
            print(f"[SIMULATION] Updated settings: {self.current_settings}")
            return True

        if not self.client or not self.client.is_connected:
            return False

        csv_str = ",".join(str(v) for v in settings_list)
        try:
            await self.client.write_gatt_char(BLE_SETTINGS_CHAR_UUID, csv_str.encode("utf-8"), response=True)
            print(f"[+] Written new settings to ESP32: {csv_str}")
            return True
        except Exception as exc:
            print(f"[!] Error writing settings: {exc}")
            return False

    async def start_distance_stream(self, callback: Callable[[int], None]):
        """Subscribe to distance notifications."""
        self.notification_callback = callback
        self._running = True

        if self.simulate:
            self._sim_task = asyncio.create_task(self._simulate_stream())
            return

        def _on_notify(sender, data: bytearray):
            try:
                dist_str = data.decode("utf-8").strip()
                dist_val = int(dist_str)
                if self.notification_callback:
                    self.notification_callback(dist_val)
            except Exception:
                pass

        if self.client and self.client.is_connected:
            await self.client.start_notify(BLE_DISTANCE_CHAR_UUID, _on_notify)

    async def stop_distance_stream(self):
        """Unsubscribe from distance notifications."""
        self._running = False
        if self._sim_task and not self._sim_task.done():
            self._sim_task.cancel()

        if self.client and self.client.is_connected and not self.simulate:
            try:
                await self.client.stop_notify(BLE_DISTANCE_CHAR_UUID)
            except Exception:
                pass

    async def disconnect(self):
        """Disconnect GATT client."""
        await self.stop_distance_stream()
        if self.client and self.client.is_connected and not self.simulate:
            await self.client.disconnect()
        self.is_connected = False
        print("[*] BLE Disconnected.")

    async def _simulate_stream(self):
        """Generate realistic vehicle reverse approach trajectory for testing."""
        # Simulated approach: starting at 950mm, slowly backing up to 25mm, pausing, then clearing
        trajectory = (
            [950, 920, 890, 850, 820] +             # SAFE_CLEAR
            [780, 720, 650, 580, 500, 430] +        # FAR_ZONE
            [390, 350, 310, 260, 210, 170] +        # MID_ZONE
            [140, 120, 95, 75, 50, 38] +            # CLOSE_ZONE
            [28, 24, 20, 20, 22] +                  # DANGER_SOLID
            [110, 250, 550, 900]                    # Pulling forward
        )

        idx = 0
        while self._running:
            dist = trajectory[idx % len(trajectory)]
            idx += 1
            if self.notification_callback:
                self.notification_callback(dist)
            await asyncio.sleep(0.12)  # ~8 Hz rate matching ESP32 loop
