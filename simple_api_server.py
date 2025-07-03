#!/usr/bin/env python3
"""
Simple API server for Phase 7C clean architecture.
Serves hearing data with proper titles.
"""

import sqlite3
from flask import Flask, jsonify
from flask_cors import CORS
from pathlib import Path
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Database path
DB_PATH = Path(__file__).parent / 'data' / 'demo_enhanced_ui.db'

def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/committees/<committee_code>/hearings', methods=['GET'])
def get_committee_hearings(committee_code):
    """Get hearings for a specific committee."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get hearings for the committee
        cursor.execute('''
            SELECT 
                id,
                hearing_title,
                committee_code,
                hearing_date,
                hearing_type,
                processing_stage,
                participant_list,
                content_summary,
                created_at,
                updated_at
            FROM hearings_unified 
            WHERE committee_code = ? 
            ORDER BY hearing_date DESC
        ''', (committee_code,))
        
        rows = cursor.fetchall()
        hearings = []
        
        for row in rows:
            hearing = {
                'id': row['id'],
                'hearing_title': row['hearing_title'],
                'committee_code': row['committee_code'],
                'hearing_date': row['hearing_date'],
                'hearing_type': row['hearing_type'],
                'processing_stage': row['processing_stage'] or 'discovered',
                'participant_list': row['participant_list'],
                'content_summary': row['content_summary'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
            hearings.append(hearing)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'hearings': hearings,
            'committee_code': committee_code,
            'total': len(hearings)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'hearings': []
        }), 500

@app.route('/api/transcript-browser/hearings', methods=['GET'])
def get_transcript_hearings():
    """Get all hearings with transcript information."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # For now, return some mock transcript data
        # In a real implementation, this would query a transcripts table
        transcripts = [
            {
                'hearing_id': 1,
                'confidence': 0.95,
                'segments': [
                    {'speaker': 'Chair Cantwell', 'text': 'The hearing will come to order.'},
                    {'speaker': 'Sen. Cruz', 'text': 'Thank you, Chair Cantwell.'}
                ]
            },
            {
                'hearing_id': 3,
                'confidence': 0.88,
                'segments': [
                    {'speaker': 'Chair Warner', 'text': 'Welcome to today\'s briefing.'},
                    {'speaker': 'UNKNOWN', 'text': 'Thank you for having me.'}
                ]
            }
        ]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'transcripts': transcripts
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'transcripts': []
        }), 500

@app.route('/api/hearings/<int:hearing_id>', methods=['GET'])
def get_hearing_details(hearing_id):
    """Get details for a specific hearing."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM hearings_unified WHERE id = ?
        ''', (hearing_id,))
        
        row = cursor.fetchone()
        
        if not row:
            return jsonify({
                'success': False,
                'error': 'Hearing not found'
            }), 404
        
        hearing = {
            'id': row['id'],
            'hearing_title': row['hearing_title'],
            'committee_code': row['committee_code'],
            'hearing_date': row['hearing_date'],
            'hearing_type': row['hearing_type'],
            'processing_stage': row['processing_stage'] or 'discovered',
            'participant_list': row['participant_list'],
            'content_summary': row['content_summary'],
            'streams': row['streams'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }
        
        conn.close()
        
        return jsonify({
            'success': True,
            'hearing': hearing
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting Simple API Server for Phase 7C...")
    print("API will be available at: http://localhost:8001")
    print("Endpoints:")
    print("  - GET /api/committees/{code}/hearings")
    print("  - GET /api/transcript-browser/hearings")
    print("  - GET /api/hearings/{id}")
    print("  - GET /api/health")
    print()
    
    app.run(host='0.0.0.0', port=8001, debug=False)