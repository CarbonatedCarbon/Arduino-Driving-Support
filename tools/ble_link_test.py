#!/usr/bin/env python3
"""
BLE Link & Handshake Verification Tool (CLI Runner)
===================================================
Delegates to tools/test_ble_link.py.
Maintained for backward compatibility with command line workflows.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tests.test_ble_link import (
    main,
    verify_env_config,
    run_ble_handshake,
    STATUS_FILE,
)

if __name__ == "__main__":
    main()
