# SOP: Real-Time Terminal HUD & User Interface

## 1. Goal
Provide an intuitive, low-latency, rich terminal-based Heads-Up Display (HUD) on the Raspberry Pi / console for real-time proximity awareness and diagnostic monitoring.

## 2. Display Components
1. **Header Banner**: System status, connected device, and live timestamp.
2. **Visual Proximity Gauge**:
   - Dynamic 40-character bar graph changing colors according to zone:
     - `DANGER_SOLID`: Bright Red `[########################################]`
     - `CLOSE_ZONE`: Magenta / Red `[####################]`
     - `MID_ZONE`: Yellow `[========================]`
     - `FAR_ZONE`: Cyan / Green `[------------------------]`
     - `SAFE_CLEAR`: Dim Green `[........................................]`
3. **Zone Status Badge & Distance Readout**:
   - Current filtered distance in millimeters and centimeters.
   - Active zone name and audible buzzer state (BEEP SLOW / BEEP FAST / SOLID TONE / SILENT).
4. **Failsafe Alert Banner**:
   - Prominent blinking alert if connection drops or data becomes stale (>500ms).
5. **Interactive Controls & Keyboard Shortcuts**:
   - `[q]`: Quit gracefully, flushing session facts.
   - `[r]`: Reset settings.
   - `[Ctrl+C]`: Exit safely.

## 3. Refresh Rate & Rendering
- Non-blocking loop refreshing at 10–20 Hz (50–100ms) to ensure smooth animations without console flickering.

## 4. Architectural Invariant & Self-Annealing Note (Cross-Platform Terminal Compatibility)
- **Windows Terminal Encoding**: Windows terminals defaulting to `cp1252` will raise `UnicodeEncodeError` when emitting multi-byte UTF-8 glyphs (emojis, complex box borders).
- **Mandatory Practice**: In `TerminalHUD.__init__`, explicitly call `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` and utilize ASCII-safe borders (`+`, `-`, `|`, `#`, `=`) for visual bars and banners. This guarantees uniform, crash-free rendering across Linux (Raspberry Pi OS) and Windows.
