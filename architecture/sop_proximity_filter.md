# SOP: Proximity Signal Filtering & Hysteresis

## 1. Goal
Provide smooth, reliable distance estimation and deterministic zone classification from raw ultrasonic/ToF sensor readings, eliminating sensor jitter and false zone transitions.

## 2. Inputs
- `raw_distance_mm` (int): Raw distance in millimeters from BLE notification or sensor read.
- `thresholds` (dict):
  - `distance_max_warning_mm`: Boundary beyond which buzzer is silent (default: 800 mm)
  - `distance_mid_zone_mm`: Threshold for moderate beeps (default: 400 mm)
  - `distance_close_zone_mm`: Threshold for rapid beeps (default: 150 mm)
  - `distance_solid_tone_mm`: Threshold for continuous solid tone (default: 30 mm)
- `hysteresis_mm` (int): Boundary buffer band (default: 20 mm).

## 3. Algorithm & Logic
1. **Outlier / Jitter Rejection (Median Filter)**:
   - Maintain a sliding window of the last 3 valid readings.
   - Filtered distance is the median of the 3 readings.
   - Ignore negative values or readings > 4000 mm.
2. **Hysteresis Zone Classification**:
   - Current zone is preserved unless distance passes the threshold by $\pm \text{hysteresis\_mm}$.
   - **Transition closer**: requires distance $\le \text{Threshold}$.
   - **Transition farther**: requires distance $> (\text{Threshold} + \text{hysteresis\_mm})$.
3. **Zones**:
   - `SAFE_CLEAR`: Distance $> \text{Max Warning}$ (or $\le 0$)
   - `FAR_ZONE`: $\text{Mid Zone} < \text{Distance} \le \text{Max Warning}$
   - `MID_ZONE`: $\text{Close Zone} < \text{Distance} \le \text{Mid Zone}$
   - `CLOSE_ZONE`: $\text{Solid Tone} < \text{Distance} \le \text{Close Zone}$
   - `DANGER_SOLID`: $\text{Distance} \le \text{Solid Tone}$
4. **Stale Data Watchdog**:
   - If time elapsed since last raw reading $> 500\text{ ms}$, zone transitions immediately to `DISCONNECTED` with `signal_status = STALE`.

## 4. Edge Cases
- Distance `0` or negative: treated as invalid/out of range, buzzer off.
- Missing readings / BLE packet loss: watchdog triggers failsafe after 500ms.
