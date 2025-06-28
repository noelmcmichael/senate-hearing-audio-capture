#!/usr/bin/env python3
"""
Data service for the Senate hearing dashboard.
Aggregates extraction results and provides API endpoints.
"""

import json
import glob
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import re
from dataclasses import dataclass
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS


@dataclass
class ExtractionRecord:
    """Single extraction record."""
    timestamp: str
    hearing_name: str
    committee: str
    url: str
    duration_seconds: float
    file_size_bytes: int
    file_path: str
    format: str
    quality: str
    success: bool
    error_message: str = None


class DataService:
    """Service to aggregate and serve extraction data."""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path('output')
        
    def load_all_results(self) -> List[ExtractionRecord]:
        """Load all extraction results from JSON files."""
        records = []
        
        # Find all results JSON files
        result_files = glob.glob(str(self.output_dir / 'results_*.json'))
        
        for file_path in result_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Extract timestamp from filename
                filename = Path(file_path).name
                timestamp_match = re.search(r'results_(\d{8}_\d{6})\.json', filename)
                timestamp = timestamp_match.group(1) if timestamp_match else 'unknown'
                
                # Handle both single results and arrays
                results_data = data if isinstance(data, list) else [data]
                
                for result_data in results_data:
                    record = self._parse_result_record(result_data, timestamp)
                    if record:
                        records.append(record)
                        
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
                continue
        
        return sorted(records, key=lambda x: x.timestamp, reverse=True)
    
    def _parse_result_record(self, data: Dict, timestamp: str) -> ExtractionRecord:
        """Parse a single result record."""
        try:
            stream = data.get('stream', {})
            result = data.get('result', {})
            
            # Extract committee from URL
            url = stream.get('metadata', {}).get('original_page', '') or stream.get('url', '')
            committee = self._extract_committee_from_url(url)
            
            # Extract hearing name from title or URL
            hearing_name = stream.get('title', '') or self._extract_name_from_url(url)
            
            return ExtractionRecord(
                timestamp=timestamp,
                hearing_name=hearing_name,
                committee=committee,
                url=url,
                duration_seconds=result.get('duration_seconds', 0),
                file_size_bytes=result.get('file_size_bytes', 0),
                file_path=result.get('output_path', ''),
                format=result.get('metadata', {}).get('format', 'unknown'),
                quality=result.get('metadata', {}).get('quality', 'unknown'),
                success=result.get('success', False),
                error_message=result.get('error_message')
            )
            
        except Exception as e:
            print(f"Error parsing record: {e}")
            return None
    
    def _extract_committee_from_url(self, url: str) -> str:
        """Extract committee name from URL."""
        if 'commerce.senate.gov' in url:
            return 'Commerce'
        elif 'judiciary.senate.gov' in url:
            return 'Judiciary'
        elif 'intelligence.senate.gov' in url:
            return 'Intelligence'
        elif 'banking.senate.gov' in url:
            return 'Banking'
        elif 'finance.senate.gov' in url:
            return 'Finance'
        elif 'help.senate.gov' in url:
            return 'HELP'
        elif 'armed-services.senate.gov' in url:
            return 'Armed Services'
        elif 'foreign.senate.gov' in url:
            return 'Foreign Relations'
        elif 'hsgac.senate.gov' in url:
            return 'Homeland Security'
        elif 'epw.senate.gov' in url:
            return 'Environment'
        else:
            return 'Unknown'
    
    def _extract_name_from_url(self, url: str) -> str:
        """Extract hearing name from URL."""
        try:
            # Get the last part of the path
            path_parts = url.rstrip('/').split('/')
            if len(path_parts) >= 2:
                name_part = path_parts[-1]
                # Clean up the name
                name = name_part.replace('-', ' ').replace('_', ' ')
                # Remove numbers and clean up
                name = re.sub(r'_?\d+$', '', name)
                return name.title()
            return 'Unknown Hearing'
        except:
            return 'Unknown Hearing'
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get aggregated data for dashboard."""
        records = self.load_all_results()
        
        # Calculate statistics
        total_extractions = len(records)
        successful_extractions = len([r for r in records if r.success])
        total_duration_hours = sum(r.duration_seconds for r in records if r.success) / 3600
        total_size_gb = sum(r.file_size_bytes for r in records if r.success) / (1024**3)
        
        # Committee breakdown
        committee_stats = {}
        for record in records:
            if record.success:
                committee_stats[record.committee] = committee_stats.get(record.committee, 0) + 1
        
        # Multi-committee coverage data
        all_committees = ['Commerce', 'Intelligence', 'Banking', 'Judiciary', 'Finance', 
                         'Armed Services', 'HELP', 'Foreign Relations', 'Homeland Security', 'Environment']
        isvp_compatible = ['Commerce', 'Intelligence', 'Banking', 'Judiciary']
        active_committees = len([c for c in committee_stats.keys() if c in isvp_compatible])
        
        committee_coverage = {
            'total_committees': len(all_committees),
            'isvp_compatible': len(isvp_compatible),
            'active_committees': active_committees,
            'coverage_percentage': round((len(isvp_compatible) / len(all_committees)) * 100, 1)
        }
        
        # Recent extractions (last 10)
        recent_extractions = []
        for record in records[:10]:
            recent_extractions.append({
                'timestamp': record.timestamp,
                'hearing_name': record.hearing_name,
                'committee': record.committee,
                'duration_minutes': round(record.duration_seconds / 60, 1) if record.success else 0,
                'file_size_mb': round(record.file_size_bytes / (1024**2), 1) if record.success else 0,
                'format': record.format,
                'success': record.success,
                'error_message': record.error_message
            })
        
        return {
            'summary': {
                'total_extractions': total_extractions,
                'successful_extractions': successful_extractions,
                'success_rate': round(successful_extractions / total_extractions * 100, 1) if total_extractions > 0 else 0,
                'total_duration_hours': round(total_duration_hours, 1),
                'total_size_gb': round(total_size_gb, 2),
                'avg_compression_ratio': self._calculate_avg_compression()
            },
            'committee_stats': committee_stats,
            'committee_coverage': committee_coverage,
            'recent_extractions': recent_extractions,
            'last_updated': datetime.now().isoformat()
        }
    
    def _calculate_avg_compression(self) -> float:
        """Calculate average compression ratio (MP3 vs estimated WAV)."""
        records = [r for r in self.load_all_results() if r.success and r.format == 'mp3']
        if not records:
            return 0
        
        # Estimate WAV size: duration * 44100 * 2 channels * 2 bytes
        compression_ratios = []
        for record in records:
            estimated_wav_size = record.duration_seconds * 44100 * 2 * 2
            if estimated_wav_size > 0:
                compression_ratio = (1 - record.file_size_bytes / estimated_wav_size) * 100
                compression_ratios.append(compression_ratio)
        
        return round(sum(compression_ratios) / len(compression_ratios), 1) if compression_ratios else 0


# Flask API
def create_app():
    app = Flask(__name__)
    CORS(app)
    
    data_service = DataService()
    
    @app.route('/api/dashboard')
    def get_dashboard_data():
        return jsonify(data_service.get_dashboard_data())
    
    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})
    
    # Serve React app
    @app.route('/')
    def serve_react_app():
        return send_from_directory('../dashboard/build', 'index.html')
    
    @app.route('/<path:path>')
    def serve_react_assets(path):
        return send_from_directory('../dashboard/build', path)
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)