#!/usr/bin/env python3
"""
Start the enhanced API server for Phase 7B.
"""
import sys
import os
from pathlib import Path
import uvicorn

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Now import and create the app
from api.main_app import EnhancedUIApp

def create_app():
    """Create the FastAPI application."""
    app_instance = EnhancedUIApp()
    return app_instance.app

if __name__ == "__main__":
    print("🚀 Starting Phase 7B Enhanced UI API Server...")
    print("Dashboard will be available at: http://localhost:8001")
    print("API docs: http://localhost:8001/api/docs")
    print()
    
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)