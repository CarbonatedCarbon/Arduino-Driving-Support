"""
Pytest configuration and shared fixtures for ReverseCam test suite.
"""

import sys
from pathlib import Path

# Ensure project root is at the front of sys.path for all tests
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
