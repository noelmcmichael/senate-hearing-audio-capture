#!/usr/bin/env python3
"""
Simple API server for Phase 7C clean architecture.
Serves hearing data with proper titles.
"""

import sqlite3
from flask import Flask, jsonify, request
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

@app.route('/api/hearings', methods=['GET'])
def get_all_hearings():
    """Get all hearings."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all hearings with status != 'sample'
        cursor.execute('''
            SELECT 
                id,
                hearing_title,
                committee_code,
                hearing_date,
                hearing_type,
                status,
                processing_stage,
                streams,
                participant_list,
                content_summary,
                full_text_content,
                created_at,
                updated_at
            FROM hearings_unified 
            WHERE status != 'sample' OR status IS NULL
            ORDER BY hearing_date DESC
        ''')
        
        rows = cursor.fetchall()
        hearings = []
        
        for row in rows:
            # Parse streams JSON if exists
            streams = {}
            if row['streams']:
                try:
                    streams = json.loads(row['streams'])
                except:
                    streams = {}
            
            hearing = {
                'id': row['id'],
                'hearing_title': row['hearing_title'],
                'committee_code': row['committee_code'],
                'hearing_date': row['hearing_date'],
                'hearing_type': row['hearing_type'],
                'status': row['status'] or 'new',
                'processing_stage': row['processing_stage'] or 'discovered',
                'streams': streams,
                'has_streams': bool(streams),
                'participant_list': row['participant_list'],
                'content_summary': row['content_summary'],
                'full_text_content': row['full_text_content'],
                'has_transcript': bool(row['full_text_content']),
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
            hearings.append(hearing)
        
        conn.close()
        
        return jsonify(hearings)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'hearings': []
        }), 500

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
        import os
        import glob
        
        # Load transcript files from the output directory
        transcript_dir = Path(__file__).parent / 'output' / 'demo_transcription'
        transcript_files = glob.glob(str(transcript_dir / 'hearing_*_transcript.json'))
        
        transcripts = []
        for file_path in transcript_files:
            try:
                with open(file_path, 'r') as f:
                    transcript_data = json.load(f)
                    transcripts.append(transcript_data)
            except Exception as e:
                print(f"Error loading transcript {file_path}: {e}")
                continue
        
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
            'full_text_content': row['full_text_content'],
            'has_transcript': bool(row['full_text_content']),
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

@app.route('/api/hearings/<int:hearing_id>/transcript', methods=['GET'])
def get_hearing_transcript(hearing_id):
    """Get transcript for a specific hearing."""
    try:
        import os
        import glob
        
        # Load transcript file for this hearing
        transcript_dir = Path(__file__).parent / 'output' / 'demo_transcription'
        transcript_file = transcript_dir / f'hearing_{hearing_id}_transcript.json'
        
        if not transcript_file.exists():
            return jsonify({
                'success': False,
                'error': 'Transcript not found for this hearing'
            }), 404
        
        with open(transcript_file, 'r') as f:
            transcript_data = json.load(f)
        
        return jsonify({
            'success': True,
            'transcript': transcript_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/hearings/<int:hearing_id>/transcript', methods=['PUT'])
def update_hearing_transcript(hearing_id):
    """Update transcript for a specific hearing with speaker assignments."""
    try:
        import os
        
        data = request.get_json()
        if not data or 'segments' not in data:
            return jsonify({
                'success': False,
                'error': 'Segments data required'
            }), 400
        
        # Load transcript file for this hearing
        transcript_dir = Path(__file__).parent / 'output' / 'demo_transcription'
        transcript_file = transcript_dir / f'hearing_{hearing_id}_transcript.json'
        
        if not transcript_file.exists():
            return jsonify({
                'success': False,
                'error': 'Transcript not found for this hearing'
            }), 404
        
        # Load existing transcript
        with open(transcript_file, 'r') as f:
            transcript_data = json.load(f)
        
        # Update segments with new speaker assignments
        transcript_data['segments'] = data['segments']
        transcript_data['updated_at'] = datetime.now().isoformat()
        
        # Save updated transcript
        with open(transcript_file, 'w') as f:
            json.dump(transcript_data, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'Transcript updated successfully',
            'transcript': transcript_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/hearings/<int:hearing_id>/capture', methods=['POST'])
def capture_hearing_audio(hearing_id):
    """Trigger audio capture for a specific hearing."""
    try:
        # Simulate capture process
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if hearing exists
        cursor.execute('SELECT id, hearing_title FROM hearings_unified WHERE id = ?', (hearing_id,))
        hearing = cursor.fetchone()
        
        if not hearing:
            return jsonify({
                'success': False,
                'error': 'Hearing not found'
            }), 404
        
        # Update status to indicate capture is in progress
        cursor.execute('''
            UPDATE hearings_unified 
            SET status = 'processing', 
                processing_stage = 'captured',
                updated_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), hearing_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Audio capture initiated for hearing: {hearing["hearing_title"]}',
            'hearing_id': hearing_id,
            'status': 'processing'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/hearings/<int:hearing_id>/pipeline/analyze', methods=['POST'])
def analyze_hearing(hearing_id):
    """Trigger analysis for a specific hearing."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if hearing exists and is in correct state
        cursor.execute('SELECT id, hearing_title, processing_stage FROM hearings_unified WHERE id = ?', (hearing_id,))
        hearing = cursor.fetchone()
        
        if not hearing:
            return jsonify({
                'success': False,
                'error': 'Hearing not found'
            }), 404
        
        if hearing['processing_stage'] != 'discovered':
            return jsonify({
                'success': False,
                'error': f'Hearing must be in "discovered" stage to analyze. Current stage: {hearing["processing_stage"]}'
            }), 400
        
        # Update to analyzed stage
        cursor.execute('''
            UPDATE hearings_unified 
            SET status = 'processing', 
                processing_stage = 'analyzed',
                updated_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), hearing_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Analysis initiated for hearing: {hearing["hearing_title"]}',
            'hearing_id': hearing_id,
            'previous_stage': 'discovered',
            'current_stage': 'analyzed'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/hearings/<int:hearing_id>/pipeline/transcribe', methods=['POST'])
def transcribe_hearing(hearing_id):
    """Trigger transcription for a specific hearing with progress tracking."""
    try:
        from enhanced_transcription_service import EnhancedTranscriptionService
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if hearing exists and is in correct state
        cursor.execute('SELECT id, hearing_title, processing_stage FROM hearings_unified WHERE id = ?', (hearing_id,))
        hearing = cursor.fetchone()
        
        if not hearing:
            return jsonify({
                'success': False,
                'error': 'Hearing not found'
            }), 404
        
        if hearing['processing_stage'] != 'captured':
            return jsonify({
                'success': False,
                'error': f'Hearing must be in "captured" stage to transcribe. Current stage: {hearing["processing_stage"]}'
            }), 400
        
        # Create enhanced transcription service
        transcription_service = EnhancedTranscriptionService()
        
        # Track progress with callback
        progress_data = {
            'stage': 'starting',
            'percent': 0,
            'message': 'Initializing transcription...'
        }
        
        def progress_callback(stage, percent, message):
            progress_data['stage'] = stage
            progress_data['percent'] = percent
            progress_data['message'] = message
            print(f"Progress: {stage} - {percent}% - {message}")
        
        try:
            transcript_data = transcription_service.transcribe_hearing(hearing_id, progress_callback=progress_callback)
            
            # Update to transcribed stage
            cursor.execute('''
                UPDATE hearings_unified 
                SET status = 'processing', 
                    processing_stage = 'transcribed',
                    updated_at = ?
                WHERE id = ?
            ''', (datetime.now().isoformat(), hearing_id))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'Transcription completed for hearing: {hearing["hearing_title"]}',
                'hearing_id': hearing_id,
                'previous_stage': 'captured',
                'current_stage': 'transcribed',
                'transcript_segments': len(transcript_data['transcription']['segments']),
                'transcript_duration': transcript_data['transcription']['duration'],
                'transcript_characters': len(transcript_data['transcription']['text']),
                'processing_method': transcript_data['metadata']['source'],
                'chunks_processed': transcript_data['metadata'].get('total_chunks', 1)
            })
            
        except Exception as transcription_error:
            conn.close()
            return jsonify({
                'success': False,
                'error': f'Transcription failed: {str(transcription_error)}'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/hearings/<int:hearing_id>/transcription/progress', methods=['GET'])
def get_transcription_progress(hearing_id):
    """Get detailed transcription progress for a specific hearing."""
    try:
        from progress_tracker import progress_tracker
        
        # Get detailed progress from tracker
        progress_data = progress_tracker.get_progress(hearing_id)
        
        # Get hearing info from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, hearing_title, processing_stage, updated_at FROM hearings_unified WHERE id = ?', (hearing_id,))
        hearing = cursor.fetchone()
        conn.close()
        
        if not hearing:
            return jsonify({
                'success': False,
                'error': 'Hearing not found'
            }), 404
        
        # If we have detailed progress data, use it
        if progress_data:
            return jsonify({
                'success': True,
                'hearing_id': hearing_id,
                'hearing_title': hearing['hearing_title'],
                'processing_stage': hearing['processing_stage'],
                'detailed_progress': {
                    'stage': progress_data['stage'],
                    'overall_progress': progress_data['overall_progress'],
                    'message': progress_data['message'],
                    'chunk_progress': progress_data.get('chunk_progress'),
                    'estimated_time_remaining': progress_data.get('estimated_time_remaining'),
                    'error': progress_data.get('error'),
                    'started_at': progress_data.get('started_at'),
                    'last_updated': progress_data.get('last_updated'),
                    'is_chunked_processing': progress_data.get('chunk_progress') is not None
                }
            })
        
        # Fallback to basic progress based on processing stage
        progress_map = {
            'discovered': {'percent': 0, 'message': 'Hearing discovered, ready for processing'},
            'analyzed': {'percent': 10, 'message': 'Hearing analyzed, ready for capture'},
            'captured': {'percent': 20, 'message': 'Audio captured, ready for transcription'},
            'transcribed': {'percent': 100, 'message': 'Transcription completed'},
            'reviewed': {'percent': 100, 'message': 'Transcription reviewed and finalized'}
        }
        
        stage = hearing['processing_stage']
        progress = progress_map.get(stage, {'percent': 0, 'message': f'Unknown stage: {stage}'})
        
        return jsonify({
            'success': True,
            'hearing_id': hearing_id,
            'hearing_title': hearing['hearing_title'],
            'processing_stage': stage,
            'detailed_progress': {
                'stage': stage,
                'overall_progress': progress['percent'],
                'message': progress['message'],
                'chunk_progress': None,
                'estimated_time_remaining': None,
                'error': None,
                'is_chunked_processing': False
            },
            'last_updated': hearing['updated_at']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error getting transcription progress: {str(e)}'
        }), 500

@app.route('/api/hearings/<int:hearing_id>/pipeline/review', methods=['POST'])
def review_hearing(hearing_id):
    """Trigger review for a specific hearing."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if hearing exists and is in correct state
        cursor.execute('SELECT id, hearing_title, processing_stage FROM hearings_unified WHERE id = ?', (hearing_id,))
        hearing = cursor.fetchone()
        
        if not hearing:
            return jsonify({
                'success': False,
                'error': 'Hearing not found'
            }), 404
        
        if hearing['processing_stage'] != 'transcribed':
            return jsonify({
                'success': False,
                'error': f'Hearing must be in "transcribed" stage to review. Current stage: {hearing["processing_stage"]}'
            }), 400
        
        # Update to reviewed stage
        cursor.execute('''
            UPDATE hearings_unified 
            SET status = 'processing', 
                processing_stage = 'reviewed',
                updated_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), hearing_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Review initiated for hearing: {hearing["hearing_title"]}',
            'hearing_id': hearing_id,
            'previous_stage': 'transcribed',
            'current_stage': 'reviewed'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/hearings/<int:hearing_id>/pipeline/publish', methods=['POST'])
def publish_hearing(hearing_id):
    """Trigger publication for a specific hearing."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if hearing exists and is in correct state
        cursor.execute('SELECT id, hearing_title, processing_stage FROM hearings_unified WHERE id = ?', (hearing_id,))
        hearing = cursor.fetchone()
        
        if not hearing:
            return jsonify({
                'success': False,
                'error': 'Hearing not found'
            }), 404
        
        if hearing['processing_stage'] != 'reviewed':
            return jsonify({
                'success': False,
                'error': f'Hearing must be in "reviewed" stage to publish. Current stage: {hearing["processing_stage"]}'
            }), 400
        
        # Update to published stage
        cursor.execute('''
            UPDATE hearings_unified 
            SET status = 'complete', 
                processing_stage = 'published',
                updated_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), hearing_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Publication completed for hearing: {hearing["hearing_title"]}',
            'hearing_id': hearing_id,
            'previous_stage': 'reviewed',
            'current_stage': 'published'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/hearings/<int:hearing_id>/pipeline/reset', methods=['POST'])
def reset_hearing_stage(hearing_id):
    """Reset hearing to a previous stage."""
    try:
        data = request.get_json() or {}
        target_stage = data.get('stage', 'discovered')
        
        # Validate target stage
        valid_stages = ['discovered', 'analyzed', 'captured', 'transcribed', 'reviewed']
        if target_stage not in valid_stages:
            return jsonify({
                'success': False,
                'error': f'Invalid stage. Must be one of: {valid_stages}'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if hearing exists
        cursor.execute('SELECT id, hearing_title, processing_stage FROM hearings_unified WHERE id = ?', (hearing_id,))
        hearing = cursor.fetchone()
        
        if not hearing:
            return jsonify({
                'success': False,
                'error': 'Hearing not found'
            }), 404
        
        # Update to target stage
        status = 'new' if target_stage == 'discovered' else 'processing'
        cursor.execute('''
            UPDATE hearings_unified 
            SET status = ?, 
                processing_stage = ?,
                updated_at = ?
            WHERE id = ?
        ''', (status, target_stage, datetime.now().isoformat(), hearing_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Reset hearing: {hearing["hearing_title"]} to {target_stage} stage',
            'hearing_id': hearing_id,
            'previous_stage': hearing['processing_stage'],
            'current_stage': target_stage
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