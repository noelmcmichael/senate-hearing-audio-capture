#!/usr/bin/env python3
"""
Simple API starter script that handles imports properly
"""

import sys
import os
import uvicorn

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Now import and run the API
if __name__ == "__main__":
    # Run the API server
    uvicorn.run(
        "api.main_app:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )