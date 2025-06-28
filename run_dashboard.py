#!/usr/bin/env python3
"""
Dashboard runner script that starts the Flask API server.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from api.data_service import create_app

if __name__ == '__main__':
    print("🚀 Starting Senate Hearing Dashboard...")
    print("Dashboard will be available at: http://localhost:5000")
    print("API endpoints:")
    print("  - http://localhost:5000/api/dashboard")
    print("  - http://localhost:5000/api/health")
    print("\nPress Ctrl+C to stop the server")
    
    app = create_app()
    app.run(debug=True, port=5000, host='0.0.0.0')