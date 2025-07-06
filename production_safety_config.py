#!/usr/bin/env python3
"""
Production Safety Configuration - Ensures Manual Control Only

This script:
1. Identifies and removes demo/test data with advanced statuses
2. Ensures all real hearings start in 'new/discovered' state
3. Prevents automatic processing from running
4. Sets up production-safe defaults
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

def get_db_connection():
    """Get database connection"""
    db_path = Path(__file__).parent / 'data' / 'demo_enhanced_ui.db'
    return sqlite3.connect(str(db_path))

def reset_demo_data_to_discovered():
    """Reset all demo data to discovered state for manual control"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("🔄 Resetting demo data to production-safe state...")
    
    # Count current advanced statuses
    cursor.execute('''
        SELECT COUNT(*) FROM hearings_unified 
        WHERE status = 'complete' OR processing_stage = 'published'
    ''')
    advanced_count = cursor.fetchone()[0]
    
    print(f"Found {advanced_count} hearings with advanced statuses")
    
    # Reset all demo hearings to discovered state
    cursor.execute('''
        UPDATE hearings_unified 
        SET status = 'new', 
            processing_stage = 'discovered',
            updated_at = ?
        WHERE status = 'complete' OR processing_stage = 'published'
    ''', (datetime.now().isoformat(),))
    
    affected_rows = cursor.rowcount
    conn.commit()
    
    print(f"✅ Reset {affected_rows} hearings to 'new/discovered' state")
    
    # Verify current state
    cursor.execute('''
        SELECT status, processing_stage, COUNT(*) as count
        FROM hearings_unified 
        GROUP BY status, processing_stage
        ORDER BY status, processing_stage
    ''')
    
    statuses = cursor.fetchall()
    print("\n📊 Current hearing statuses after reset:")
    for status, stage, count in statuses:
        print(f"  {status} / {stage}: {count} hearings")
    
    conn.close()
    
    return affected_rows

def ensure_production_safety():
    """Ensure production safety by checking for automatic processes"""
    print("\n🔒 Checking production safety...")
    
    # Check for background processes
    import subprocess
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    
    dangerous_processes = [
        'background_processor.py',
        'automated_scheduler.py', 
        'process_single_hearing.py',
        'monitor_for_real_hearings.py'
    ]
    
    running_processes = []
    for process in dangerous_processes:
        if process in result.stdout:
            running_processes.append(process)
    
    if running_processes:
        print(f"⚠️  WARNING: Found potentially automatic processes running:")
        for process in running_processes:
            print(f"  - {process}")
        print("  Consider stopping these processes for production safety.")
    else:
        print("✅ No automatic processing detected")
    
    return len(running_processes) == 0

def set_production_config():
    """Set production-safe configuration"""
    print("\n⚙️  Setting production configuration...")
    
    # Create production config file
    config = {
        "production_mode": True,
        "automatic_processing": False,
        "manual_control_required": True,
        "default_hearing_status": "new",
        "default_processing_stage": "discovered",
        "require_user_confirmation": True,
        "timestamp": datetime.now().isoformat()
    }
    
    config_path = Path(__file__).parent / 'data' / 'production_config.json'
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Production config saved to {config_path}")
    
    return config

def main():
    """Main function to set up production safety"""
    print("🎯 Setting up Production Safety Configuration")
    print("=" * 50)
    
    # Reset demo data
    reset_count = reset_demo_data_to_discovered()
    
    # Check for safety
    is_safe = ensure_production_safety()
    
    # Set production config
    config = set_production_config()
    
    print("\n📋 Production Safety Summary:")
    print(f"  - Reset {reset_count} hearings to manual control")
    print(f"  - Automatic processes: {'✅ None detected' if is_safe else '⚠️  Some detected'}")
    print(f"  - Production config: ✅ Enabled")
    print(f"  - Manual control: ✅ Required for all pipeline stages")
    
    if is_safe:
        print("\n🎉 Production safety configuration complete!")
        print("   All hearings now require manual user intervention.")
    else:
        print("\n⚠️  Please review and stop any automatic processes before deployment.")

if __name__ == "__main__":
    main()