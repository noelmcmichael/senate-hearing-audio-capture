#!/usr/bin/env python3
"""
Senate Hearing Audio Capture Agent - Entry Point

Convenience script to run the audio capture agent from project root.
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from main import main

if __name__ == "__main__":
    sys.exit(main())