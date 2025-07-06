#!/usr/bin/env python3
"""
Progress tracking system for chunked transcription processing.
Provides real-time progress updates with detailed chunk information.
"""

import json
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable

class ProgressTracker:
    """Thread-safe progress tracking for transcription operations."""
    
    def __init__(self):
        """Initialize progress tracker."""
        self.progress_data = {}
        self.lock = threading.Lock()
        self.storage_dir = Path(__file__).parent / 'data' / 'progress'
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def start_operation(self, hearing_id: int, operation_type: str = 'transcription'):
        """Start tracking progress for a new operation."""
        with self.lock:
            self.progress_data[hearing_id] = {
                'operation_type': operation_type,
                'started_at': datetime.now().isoformat(),
                'stage': 'initializing',
                'overall_progress': 0,
                'message': 'Initializing operation...',
                'chunk_progress': None,
                'estimated_time_remaining': None,
                'error': None,
                'completed_at': None
            }
            self._save_progress(hearing_id)
    
    def update_progress(self, hearing_id: int, stage: str, overall_progress: int, 
                       message: str, chunk_progress: Optional[Dict] = None,
                       estimated_time_remaining: Optional[int] = None,
                       error: Optional[str] = None):
        """Update progress for a specific hearing."""
        with self.lock:
            if hearing_id in self.progress_data:
                self.progress_data[hearing_id].update({
                    'stage': stage,
                    'overall_progress': overall_progress,
                    'message': message,
                    'chunk_progress': chunk_progress,
                    'estimated_time_remaining': estimated_time_remaining,
                    'error': error,
                    'last_updated': datetime.now().isoformat()
                })
                
                # Mark as completed if at 100%
                if overall_progress >= 100 and not error:
                    self.progress_data[hearing_id]['completed_at'] = datetime.now().isoformat()
                
                self._save_progress(hearing_id)
    
    def get_progress(self, hearing_id: int) -> Optional[Dict[str, Any]]:
        """Get current progress for a hearing."""
        with self.lock:
            return self.progress_data.get(hearing_id, None)
    
    def complete_operation(self, hearing_id: int, success: bool = True, error: Optional[str] = None):
        """Mark operation as completed."""
        with self.lock:
            if hearing_id in self.progress_data:
                self.progress_data[hearing_id].update({
                    'stage': 'completed' if success else 'failed',
                    'overall_progress': 100 if success else self.progress_data[hearing_id]['overall_progress'],
                    'completed_at': datetime.now().isoformat(),
                    'error': error
                })
                self._save_progress(hearing_id)
    
    def clear_progress(self, hearing_id: int):
        """Clear progress data for a hearing."""
        with self.lock:
            if hearing_id in self.progress_data:
                del self.progress_data[hearing_id]
                progress_file = self.storage_dir / f'hearing_{hearing_id}_progress.json'
                if progress_file.exists():
                    progress_file.unlink()
    
    def _save_progress(self, hearing_id: int):
        """Save progress to disk for persistence."""
        try:
            progress_file = self.storage_dir / f'hearing_{hearing_id}_progress.json'
            with open(progress_file, 'w') as f:
                json.dump(self.progress_data[hearing_id], f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save progress for hearing {hearing_id}: {e}")
    
    def _load_progress(self, hearing_id: int) -> bool:
        """Load progress from disk if available."""
        try:
            progress_file = self.storage_dir / f'hearing_{hearing_id}_progress.json'
            if progress_file.exists():
                with open(progress_file, 'r') as f:
                    self.progress_data[hearing_id] = json.load(f)
                return True
            return False
        except Exception as e:
            print(f"Warning: Failed to load progress for hearing {hearing_id}: {e}")
            return False

class ChunkedProgressCallback:
    """Progress callback implementation for chunked transcription."""
    
    def __init__(self, hearing_id: int, tracker: ProgressTracker):
        """Initialize progress callback."""
        self.hearing_id = hearing_id
        self.tracker = tracker
        self.start_time = time.time()
        self.total_chunks = 0
        self.current_chunk = 0
        self.stage_weights = {
            'analyzing': 10,      # 10% for analysis
            'chunking': 15,       # 15% for chunking
            'processing': 70,     # 70% for transcription processing
            'merging': 15,        # 15% for merging
            'cleanup': 5          # 5% for cleanup
        }
    
    def __call__(self, stage: str, progress: int, message: str, **kwargs):
        """Handle progress callback from transcription service."""
        # Calculate overall progress based on stage and weights
        overall_progress = self._calculate_overall_progress(stage, progress)
        
        # Handle chunk-specific progress
        chunk_progress = None
        if stage.startswith('processing_chunk'):
            chunk_info = self._parse_chunk_stage(stage)
            if chunk_info:
                self.current_chunk = chunk_info['current']
                self.total_chunks = chunk_info['total']
                chunk_progress = {
                    'current_chunk': self.current_chunk,
                    'total_chunks': self.total_chunks,
                    'chunk_progress': progress
                }
        
        # Calculate estimated time remaining
        estimated_time = self._calculate_estimated_time(overall_progress)
        
        # Update progress
        self.tracker.update_progress(
            self.hearing_id,
            stage=stage,
            overall_progress=overall_progress,
            message=message,
            chunk_progress=chunk_progress,
            estimated_time_remaining=estimated_time
        )
    
    def _calculate_overall_progress(self, stage: str, stage_progress: int) -> int:
        """Calculate overall progress based on stage weights."""
        base_progress = 0
        
        if stage == 'analyzing':
            base_progress = 0
        elif stage == 'chunking':
            base_progress = self.stage_weights['analyzing']
        elif stage.startswith('processing'):
            base_progress = self.stage_weights['analyzing'] + self.stage_weights['chunking']
        elif stage == 'merging':
            base_progress = (self.stage_weights['analyzing'] + 
                           self.stage_weights['chunking'] + 
                           self.stage_weights['processing'])
        elif stage == 'cleanup':
            base_progress = (self.stage_weights['analyzing'] + 
                           self.stage_weights['chunking'] + 
                           self.stage_weights['processing'] + 
                           self.stage_weights['merging'])
        elif stage == 'completed':
            return 100
        
        # Add stage-specific progress
        if stage == 'analyzing':
            current_stage_weight = self.stage_weights['analyzing']
        elif stage == 'chunking':
            current_stage_weight = self.stage_weights['chunking']
        elif stage.startswith('processing'):
            current_stage_weight = self.stage_weights['processing']
        elif stage == 'merging':
            current_stage_weight = self.stage_weights['merging']
        elif stage == 'cleanup':
            current_stage_weight = self.stage_weights['cleanup']
        else:
            current_stage_weight = 0
        
        stage_contribution = (stage_progress / 100) * current_stage_weight
        overall = min(100, int(base_progress + stage_contribution))
        
        return overall
    
    def _parse_chunk_stage(self, stage: str) -> Optional[Dict[str, int]]:
        """Parse chunk information from stage string."""
        # Expected format: "processing_chunk_X_of_Y"
        try:
            parts = stage.split('_')
            if len(parts) >= 5 and parts[0] == 'processing' and parts[1] == 'chunk':
                current = int(parts[2])
                total = int(parts[4])
                return {'current': current, 'total': total}
        except (ValueError, IndexError):
            pass
        return None
    
    def _calculate_estimated_time(self, overall_progress: int) -> Optional[int]:
        """Calculate estimated time remaining based on current progress."""
        if overall_progress <= 0:
            return None
        
        elapsed_time = time.time() - self.start_time
        if elapsed_time < 10:  # Too early to estimate
            return None
        
        # Calculate time per percent and estimate remaining
        time_per_percent = elapsed_time / overall_progress
        remaining_percent = 100 - overall_progress
        estimated_remaining = int(time_per_percent * remaining_percent)
        
        return estimated_remaining

# Global progress tracker instance
progress_tracker = ProgressTracker()