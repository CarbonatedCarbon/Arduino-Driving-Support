#!/usr/bin/env python3
"""
Layer 3 Tool: Terminal HUD & Proximity Visualizer
=================================================
Renders an automotive Heads-Up Display (HUD) in terminal.
Features ANSI color-coded proximity bar, zone badges, buzzer status,
and real-time session telemetry.
Equipped with cross-platform UTF-8 safe stdout reconfiguration.
"""

import os
import sys
from typing import Dict, Any, Optional

# ANSI Color Codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"

BG_RED = "\033[41m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"


class TerminalHUD:
    def __init__(self):
        # Configure stdout for UTF-8 on Windows
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

        if os.name == "nt":
            os.system("")

    def clear_screen(self):
        """Move cursor to top-left and clear terminal buffer."""
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

    def render(
        self,
        telemetry: Dict[str, Any],
        session_info: Optional[Dict[str, Any]] = None,
        is_simulated: bool = False,
    ):
        """Render the complete HUD frame."""
        zone = telemetry.get("zone", "DISCONNECTED")
        dist_mm = telemetry.get("filtered_distance_mm", 0)
        raw_mm = telemetry.get("raw_distance_mm", 0)
        volume = telemetry.get("buzzer_volume_pct", 0)
        signal = telemetry.get("signal_status", "UNKNOWN")

        # Determine zone colors and bar aesthetics
        zone_color = GREEN
        zone_label = "SAFE / CLEAR"
        tone_description = f"{DIM}Silent (0%){RESET}"
        bar_fill_char = "="

        if zone == "DANGER_SOLID":
            zone_color = RED + BOLD
            zone_label = "[!] CRITICAL: STOP NOW!"
            tone_description = f"{BG_RED}{WHITE}{BOLD} SOLID TONE ({volume}%) {RESET}"
            bar_fill_char = "#"
        elif zone == "CLOSE_ZONE":
            zone_color = MAGENTA + BOLD
            zone_label = "[!] CLOSE PROXIMITY"
            tone_description = f"{MAGENTA}{BOLD}RAPID BEEPS (100ms, {volume}%){RESET}"
            bar_fill_char = "#"
        elif zone == "MID_ZONE":
            zone_color = YELLOW + BOLD
            zone_label = "[*] APPROACHING"
            tone_description = f"{YELLOW}MODERATE BEEPS (300ms, {volume}%){RESET}"
            bar_fill_char = "="
        elif zone == "FAR_ZONE":
            zone_color = CYAN
            zone_label = "[i] WARNING ZONE"
            tone_description = f"{CYAN}SLOW BEEPS (600ms, {volume}%){RESET}"
            bar_fill_char = "-"
        elif zone == "DISCONNECTED":
            zone_color = RED + BOLD
            zone_label = "[X] SENSOR DISCONNECTED / STALE"
            tone_description = f"{DIM}Buzzer Suppressed{RESET}"

        # Calculate 40-character bar graph (scaled 0mm to 800mm)
        max_scale = 800
        clamped_dist = max(0, min(dist_mm, max_scale))
        if dist_mm <= 0 or zone in ("SAFE_CLEAR", "DISCONNECTED"):
            filled_len = 0
        else:
            filled_len = int(((max_scale - clamped_dist) / max_scale) * 40)
            filled_len = max(1, min(filled_len, 40))

        bar_graphic = f"{zone_color}{bar_fill_char * filled_len}{RESET}{DIM}{'.' * (40 - filled_len)}{RESET}"

        # Session metrics
        min_clearance = "--"
        solid_count = "0"
        readings = "0"
        if session_info:
            min_c = session_info.get("min_distance_mm", 9999)
            min_clearance = f"{min_c} mm" if min_c != 9999 else "--"
            solid_count = str(session_info.get("solid_tone_triggers", 0))
            readings = str(session_info.get("readings_count", 0))

        mode_badge = f"{YELLOW}[SIMULATION]{RESET}" if is_simulated else f"{GREEN}[BLE LIVE]{RESET}"

        lines = [
            f"\033[H",
            f"{BOLD}+--------------------------------------------------------------------+{RESET}",
            f"{BOLD}|              REVERSE-CAM PROXIMITY TERMINAL HUD                    |{RESET}",
            f"{BOLD}+--------------------------------------------------------------------+{RESET}",
            f" Mode: {mode_badge}   Signal: {GREEN if signal == 'HEALTHY' else RED}{signal}{RESET}   Time: {DIM}{telemetry.get('timestamp_iso', '')[:19]}{RESET}",
            f"-" * 70,
            f"  ZONE: {zone_color}{zone_label:<32}{RESET} BUZZER: {tone_description}",
            f"",
            f"  CLEARANCE:   {BOLD}{dist_mm:>5} mm{RESET} ({dist_mm / 10:>5.1f} cm)   [Raw Sensor: {raw_mm:>5} mm]",
            f"",
            f"  CLOSE  < {bar_graphic} >  FAR",
            f"          0mm                                       800mm",
            f"-" * 70,
            f"  {BOLD}SESSION METRICS:{RESET}",
            f"    * Minimum Clearance: {BOLD}{min_clearance:<10}{RESET}   * Solid Tone Alerts: {BOLD}{solid_count:<6}{RESET}",
            f"    * Samples Processed: {BOLD}{readings:<10}{RESET}   * Cube Fact Sync:   {CYAN}LOCAL_STORED{RESET}",
            f"-" * 70,
            f"  Controls: [q] Quit & Save Fact   [r] Reset Settings   [Ctrl+C] Exit",
        ]

        sys.stdout.write("\n".join(lines) + "\n")
        sys.stdout.flush()
