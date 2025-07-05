"""
Simple admin bootstrap endpoint to add to the service.
This will create committees directly in the database through the service.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import asyncio
import asyncpg
import json
import os
from datetime import datetime

router = APIRouter()

# Default committees for bootstrap
DEFAULT_COMMITTEES = [
    {
        'committee_code': 'SCOM',
        'committee_name': 'Senate Committee on Commerce, Science, and Transportation',
        'chamber': 'Senate',
        'total_members': 28,
        'majority_party': 'Democrat',
        'minority_party': 'Republican',
        'metadata': {
            'description': 'Committee with jurisdiction over commerce, science, and transportation',
            'website': 'https://www.commerce.senate.gov',
            'isvp_compatible': True
        }
    },
    {
        'committee_code': 'SSCI',
        'committee_name': 'Senate Select Committee on Intelligence',
        'chamber': 'Senate',
        'total_members': 21,
        'majority_party': 'Democrat',
        'minority_party': 'Republican',
        'metadata': {
            'description': 'Select committee overseeing intelligence community',
            'website': 'https://www.intelligence.senate.gov',
            'isvp_compatible': True
        }
    },
    {
        'committee_code': 'SSJU',
        'committee_name': 'Senate Committee on the Judiciary',
        'chamber': 'Senate',
        'total_members': 22,
        'majority_party': 'Democrat',
        'minority_party': 'Republican',
        'metadata': {
            'description': 'Committee with jurisdiction over federal judiciary',
            'website': 'https://www.judiciary.senate.gov',
            'isvp_compatible': True
        }
    }
]

async def create_committees_in_db():
    """Create committees directly in the database"""
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")
    
    try:
        conn = await asyncpg.connect(db_url)
        
        # Create committees table if it doesn't exist
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS committees (
                committee_code VARCHAR(10) PRIMARY KEY,
                committee_name VARCHAR(255) NOT NULL,
                chamber VARCHAR(10) NOT NULL,
                total_members INTEGER,
                majority_party VARCHAR(20),
                minority_party VARCHAR(20),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert committees
        committees_added = 0
        for committee in DEFAULT_COMMITTEES:
            try:
                await conn.execute("""
                    INSERT INTO committees (committee_code, committee_name, chamber, total_members, majority_party, minority_party, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (committee_code) DO UPDATE SET
                        committee_name = EXCLUDED.committee_name,
                        chamber = EXCLUDED.chamber,
                        total_members = EXCLUDED.total_members,
                        majority_party = EXCLUDED.majority_party,
                        minority_party = EXCLUDED.minority_party,
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP
                """, 
                committee['committee_code'],
                committee['committee_name'],
                committee['chamber'],
                committee['total_members'],
                committee['majority_party'],
                committee['minority_party'],
                json.dumps(committee['metadata']))
                committees_added += 1
            except Exception as e:
                print(f"Error adding committee {committee['committee_code']}: {e}")
        
        # Get final count
        count = await conn.fetchval("SELECT COUNT(*) FROM committees")
        
        await conn.close()
        
        return {
            "success": True,
            "committees_added": committees_added,
            "total_committees": count,
            "message": f"Bootstrap completed: {committees_added} committees added, {count} total committees"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/admin/bootstrap")
async def bootstrap_system():
    """Bootstrap the system with default committees"""
    try:
        result = await create_committees_in_db()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bootstrap failed: {str(e)}")

@router.get("/admin/status")
async def admin_status():
    """Check system status for admin purposes"""
    try:
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            return {"error": "DATABASE_URL not configured"}
        
        conn = await asyncpg.connect(db_url)
        
        # Check committees
        committee_count = await conn.fetchval("SELECT COUNT(*) FROM committees")
        
        # Check hearings
        hearing_count = await conn.fetchval("SELECT COUNT(*) FROM hearings")
        
        await conn.close()
        
        return {
            "status": "healthy",
            "committees": committee_count,
            "hearings": hearing_count,
            "bootstrap_needed": committee_count == 0
        }
        
    except Exception as e:
        return {"error": str(e)}

# Add these routes to main app
# app.include_router(router)