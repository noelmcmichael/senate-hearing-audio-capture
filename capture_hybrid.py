#!/usr/bin/env python3
"""
Hybrid Congressional Hearing Audio Capture - Entry Point

Enhanced capture script supporting both Senate ISVP and YouTube (House) streams
with intelligent platform detection and automatic fallback.
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from main_hybrid import main

if __name__ == "__main__":
    sys.exit(main())