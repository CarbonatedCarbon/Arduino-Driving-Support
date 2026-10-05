# SOP: BLE Client Communication & GATT Management

## 1. Goal
Manage asynchronous Bluetooth Low Energy connection between the Raspberry Pi / PC and the ESP32 `ReverseCam` peripheral, subscribing to distance notifications and synchronizing configuration settings.

## 2. Inputs & Environment
- Environment configuration from `.env`:
  - `BLE_DEVICE_NAME`: Target peripheral name (`ReverseCam`).
  - `BLE_SERVICE_UUID`: GATT service UUID (`4fafc201-1fb5-459e-8fcc-c5c9c331914b`).
  - `BLE_SETTINGS_CHAR_UUID`: Settings characteristic UUID (`beb5483e-36e1-4688-b7f5-ea07361b26a8`).
  - `BLE_DISTANCE_CHAR_UUID`: Distance characteristic UUID (`1c95d5e3-d8f7-413a-bf3d-7a2e5d7be87e`).

## 3. Operational Logic
1. **Device Discovery**:
   - Use `BleakScanner` with 5-second timeout to find peripheral matching `BLE_DEVICE_NAME`.
2. **Connection & Notification Subscription**:
   - Connect using `BleakClient`.
   - Subscribe to notifications on `BLE_DISTANCE_CHAR_UUID`.
   - Parse notification payload (UTF-8 encoded integer string in mm) and forward to proximity filter.
3. **Settings Synchronization**:
   - Read current 8-parameter CSV on connection.
   - Support writing new 8-parameter CSV with read-back verification.
4. **Auto-Reconnect & Graceful Fallback**:
   - If disconnected, stop notification handler and attempt reconnection with 2s exponential backoff up to 10s.
   - Provide Simulation/Mock mode flag `--simulate` for testing and development when physical ESP32 is powered down.

## 4. Edge Cases
- GATT write fails or receives invalid acknowledgement: retry once, log warning.
- Device disconnects abruptly: notify proximity filter to trigger `DISCONNECTED` state.
