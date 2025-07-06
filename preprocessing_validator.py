#!/usr/bin/env python3
"""
Pre-processing validation system for comprehensive readiness assessment.
Validates all requirements before starting processing to catch issues early.
"""

import os
import subprocess
import time
import requests
import asyncio
import psutil
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import keyring
import logging

logger = logging.getLogger(__name__)

class PreprocessingValidationError(Exception):
    """Custom exception for pre-processing validation failures."""
    
    def __init__(self, message: str, validation_results: Dict[str, Any]):
        super().__init__(message)
        self.validation_results = validation_results

class SystemResourceValidator:
    """Validates system resources for audio processing."""
    
    def __init__(self):
        """Initialize system resource validator."""
        self.min_free_memory_mb = 500  # Minimum free memory required
        self.min_free_disk_gb = 2      # Minimum free disk space required
        self.max_cpu_percent = 90      # Maximum CPU usage threshold
        
    async def validate_system_resources(self) -> Dict[str, Any]:
        """Validate system has sufficient resources for processing."""
        try:
            # Check memory
            memory = psutil.virtual_memory()
            available_memory_mb = memory.available / (1024 * 1024)
            
            # Check disk space
            disk_usage = psutil.disk_usage('/')
            free_disk_gb = disk_usage.free / (1024 * 1024 * 1024)
            
            # Check CPU usage (average over 1 second)
            cpu_percent = psutil.cpu_percent(interval=1.0)
            
            # Check if requirements are met
            memory_ok = available_memory_mb >= self.min_free_memory_mb
            disk_ok = free_disk_gb >= self.min_free_disk_gb
            cpu_ok = cpu_percent <= self.max_cpu_percent
            
            validation_result = {
                'valid': memory_ok and disk_ok and cpu_ok,
                'memory': {
                    'available_mb': round(available_memory_mb, 1),
                    'required_mb': self.min_free_memory_mb,
                    'sufficient': memory_ok
                },
                'disk': {
                    'free_gb': round(free_disk_gb, 1),
                    'required_gb': self.min_free_disk_gb,
                    'sufficient': disk_ok
                },
                'cpu': {
                    'usage_percent': round(cpu_percent, 1),
                    'threshold_percent': self.max_cpu_percent,
                    'acceptable': cpu_ok
                }
            }
            
            if not validation_result['valid']:
                issues = []
                if not memory_ok:
                    issues.append(f"Insufficient memory: {available_memory_mb:.1f}MB < {self.min_free_memory_mb}MB")
                if not disk_ok:
                    issues.append(f"Insufficient disk space: {free_disk_gb:.1f}GB < {self.min_free_disk_gb}GB")
                if not cpu_ok:
                    issues.append(f"High CPU usage: {cpu_percent:.1f}% > {self.max_cpu_percent}%")
                
                validation_result['error'] = f"System resource issues: {', '.join(issues)}"
            
            return validation_result
            
        except Exception as e:
            return {
                'valid': False,
                'error': f"System resource validation failed: {e}"
            }

class AudioFileValidator:
    """Validates audio files for processing readiness."""
    
    def __init__(self):
        """Initialize audio file validator."""
        self.supported_formats = ['.mp3', '.wav', '.flac', '.m4a', '.aac']
        self.max_file_size_gb = 5  # Maximum file size for processing
        self.min_duration_seconds = 5  # Minimum duration
        self.max_duration_hours = 10   # Maximum duration
        
    async def validate_audio_file(self, audio_path: str) -> Dict[str, Any]:
        """Comprehensive audio file validation."""
        try:
            audio_file = Path(audio_path)
            
            # Check file existence
            if not audio_file.exists():
                return {
                    'valid': False,
                    'error': f'Audio file not found: {audio_path}'
                }
            
            # Check file extension
            if audio_file.suffix.lower() not in self.supported_formats:
                return {
                    'valid': False,
                    'error': f'Unsupported format: {audio_file.suffix} (supported: {self.supported_formats})'
                }
            
            # Check file size
            file_size_bytes = audio_file.stat().st_size
            file_size_gb = file_size_bytes / (1024 * 1024 * 1024)
            
            if file_size_bytes == 0:
                return {
                    'valid': False,
                    'error': 'Audio file is empty'
                }
            
            if file_size_gb > self.max_file_size_gb:
                return {
                    'valid': False,
                    'error': f'File too large: {file_size_gb:.2f}GB > {self.max_file_size_gb}GB'
                }
            
            # Validate audio integrity using ffprobe
            audio_info = await self._analyze_audio_integrity(audio_path)
            
            if not audio_info['valid']:
                return audio_info
            
            # Check duration
            duration_seconds = audio_info['duration_seconds']
            duration_hours = duration_seconds / 3600
            
            if duration_seconds < self.min_duration_seconds:
                return {
                    'valid': False,
                    'error': f'Audio too short: {duration_seconds}s < {self.min_duration_seconds}s'
                }
            
            if duration_hours > self.max_duration_hours:
                return {
                    'valid': False,
                    'error': f'Audio too long: {duration_hours:.1f}h > {self.max_duration_hours}h'
                }
            
            # Calculate processing cost estimate
            estimated_cost = self._estimate_processing_cost(file_size_gb, duration_hours)
            
            return {
                'valid': True,
                'file_info': {
                    'path': str(audio_file),
                    'size_gb': round(file_size_gb, 3),
                    'duration_seconds': round(duration_seconds, 1),
                    'duration_minutes': round(duration_seconds / 60, 1),
                    'format': audio_file.suffix.lower(),
                    'codec': audio_info.get('codec', 'unknown'),
                    'sample_rate': audio_info.get('sample_rate', 'unknown'),
                    'channels': audio_info.get('channels', 'unknown')
                },
                'processing_estimates': {
                    'estimated_cost_usd': estimated_cost,
                    'estimated_time_minutes': self._estimate_processing_time(file_size_gb, duration_hours),
                    'chunks_needed': self._estimate_chunks_needed(file_size_gb),
                    'api_calls_needed': self._estimate_chunks_needed(file_size_gb)
                }
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Audio file validation failed: {e}'
            }
    
    async def _analyze_audio_integrity(self, audio_path: str) -> Dict[str, Any]:
        """Analyze audio file integrity using ffprobe."""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                audio_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return {
                    'valid': False,
                    'error': f'ffprobe failed: {stderr.decode()}'
                }
            
            probe_data = json.loads(stdout.decode())
            
            # Extract audio stream info
            audio_streams = [s for s in probe_data.get('streams', []) if s.get('codec_type') == 'audio']
            
            if not audio_streams:
                return {
                    'valid': False,
                    'error': 'No audio streams found in file'
                }
            
            audio_stream = audio_streams[0]  # Use first audio stream
            format_info = probe_data.get('format', {})
            
            duration = float(format_info.get('duration', 0))
            
            return {
                'valid': True,
                'duration_seconds': duration,
                'codec': audio_stream.get('codec_name'),
                'sample_rate': audio_stream.get('sample_rate'),
                'channels': audio_stream.get('channels'),
                'bit_rate': format_info.get('bit_rate')
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Audio integrity analysis failed: {e}'
            }
    
    def _estimate_processing_cost(self, file_size_gb: float, duration_hours: float) -> float:
        """Estimate processing cost based on OpenAI Whisper pricing."""
        # OpenAI Whisper pricing: $0.006 per minute
        duration_minutes = duration_hours * 60
        return round(duration_minutes * 0.006, 2)
    
    def _estimate_processing_time(self, file_size_gb: float, duration_hours: float) -> float:
        """Estimate processing time based on file characteristics."""
        # Base processing time: ~0.1x real-time for transcription
        # Additional time for chunking, API calls, and merging
        base_time = duration_hours * 60 * 0.1  # 10% of real-time
        
        # Add overhead for chunking if needed
        if file_size_gb > 0.02:  # Files > 20MB need chunking
            chunks_needed = self._estimate_chunks_needed(file_size_gb)
            chunking_overhead = chunks_needed * 0.5  # 30 seconds per chunk overhead
            base_time += chunking_overhead
        
        return round(base_time, 1)
    
    def _estimate_chunks_needed(self, file_size_gb: float) -> int:
        """Estimate number of chunks needed."""
        if file_size_gb <= 0.02:  # 20MB or less
            return 1
        
        # Assume ~20MB per chunk with overlap
        chunks = int((file_size_gb * 1024) / 20) + 1
        return max(chunks, 1)

class APIAccessValidator:
    """Validates API access and credentials."""
    
    def __init__(self):
        """Initialize API access validator."""
        self.openai_api_url = "https://api.openai.com/v1/models"
        self.timeout_seconds = 30
        
    async def validate_api_access(self) -> Dict[str, Any]:
        """Validate OpenAI API access and credentials."""
        try:
            # Get API key from keyring
            api_key = self._get_openai_key()
            
            if not api_key:
                return {
                    'valid': False,
                    'error': 'OpenAI API key not found in keyring'
                }
            
            # Test API access
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # Use asyncio timeout for the request
            try:
                response = await asyncio.wait_for(
                    self._make_async_request(headers),
                    timeout=self.timeout_seconds
                )
                
                if response['status'] == 200:
                    return {
                        'valid': True,
                        'api_info': {
                            'key_valid': True,
                            'models_available': len(response.get('data', [])),
                            'whisper_available': any(
                                'whisper' in model.get('id', '') 
                                for model in response.get('data', [])
                            )
                        }
                    }
                else:
                    return {
                        'valid': False,
                        'error': f'API request failed: {response["status"]} - {response.get("error", "Unknown error")}'
                    }
                    
            except asyncio.TimeoutError:
                return {
                    'valid': False,
                    'error': f'API request timeout after {self.timeout_seconds} seconds'
                }
                
        except Exception as e:
            return {
                'valid': False,
                'error': f'API validation failed: {e}'
            }
    
    def _get_openai_key(self) -> Optional[str]:
        """Get OpenAI API key from keyring storage."""
        try:
            # Try different case variations
            for key_name in ['OpenAI Key', 'OPENAI_API_KEY', 'openai_api_key', 'OpenAI_API_KEY']:
                try:
                    key = keyring.get_password('memex', key_name)
                    if key:
                        return key
                except Exception:
                    continue
            return None
        except Exception:
            return None
    
    async def _make_async_request(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Make async HTTP request to OpenAI API."""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.openai_api_url, headers=headers) as response:
                result = {'status': response.status}
                
                if response.status == 200:
                    try:
                        result['data'] = await response.json()
                    except:
                        result['data'] = []
                else:
                    try:
                        result['error'] = await response.text()
                    except:
                        result['error'] = f"HTTP {response.status}"
                        
                return result

class HearingMetadataValidator:
    """Validates hearing metadata and database state."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize hearing metadata validator."""
        self.db_path = db_path or Path(__file__).parent / 'data' / 'demo_enhanced_ui.db'
        
    async def validate_hearing_metadata(self, hearing_id: int) -> Dict[str, Any]:
        """Validate hearing metadata exists and is complete."""
        try:
            import sqlite3
            
            if not os.path.exists(self.db_path):
                return {
                    'valid': False,
                    'error': f'Database not found: {self.db_path}'
                }
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # Check if hearing exists
                cursor.execute("SELECT * FROM hearings WHERE id = ?", (hearing_id,))
                hearing_row = cursor.fetchone()
                
                if not hearing_row:
                    return {
                        'valid': False,
                        'error': f'Hearing {hearing_id} not found in database'
                    }
                
                # Get column names
                cursor.execute("PRAGMA table_info(hearings)")
                columns = [row[1] for row in cursor.fetchall()]
                
                # Create hearing dict
                hearing = dict(zip(columns, hearing_row))
                
                # Validate required fields
                required_fields = ['title', 'committee', 'date']
                missing_fields = [field for field in required_fields if not hearing.get(field)]
                
                if missing_fields:
                    return {
                        'valid': False,
                        'error': f'Missing required fields: {missing_fields}'
                    }
                
                return {
                    'valid': True,
                    'hearing_info': {
                        'id': hearing['id'],
                        'title': hearing['title'],
                        'committee': hearing['committee'],
                        'date': hearing['date'],
                        'status': hearing.get('status', 'unknown'),
                        'has_audio': bool(hearing.get('audio_file_path'))
                    }
                }
                
            finally:
                conn.close()
                
        except Exception as e:
            return {
                'valid': False,
                'error': f'Hearing metadata validation failed: {e}'
            }

class PreprocessingValidator:
    """Comprehensive pre-processing validation system."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the pre-processing validator."""
        self.system_validator = SystemResourceValidator()
        self.audio_validator = AudioFileValidator()
        self.api_validator = APIAccessValidator()
        self.metadata_validator = HearingMetadataValidator(db_path)
        
    async def validate_processing_readiness(self, audio_path: str, hearing_id: int) -> Dict[str, Any]:
        """Validate all requirements before starting processing."""
        logger.info(f"Starting comprehensive validation for hearing {hearing_id}")
        
        # Run all validations
        validation_tasks = {
            'system_resources': self.system_validator.validate_system_resources(),
            'audio_file': self.audio_validator.validate_audio_file(audio_path),
            'api_access': self.api_validator.validate_api_access(),
            'hearing_metadata': self.metadata_validator.validate_hearing_metadata(hearing_id)
        }
        
        # Execute all validations concurrently
        validation_results = {}
        for name, task in validation_tasks.items():
            try:
                validation_results[name] = await task
            except Exception as e:
                validation_results[name] = {
                    'valid': False,
                    'error': f'Validation task failed: {e}'
                }
        
        # Check overall validation status
        overall_valid = all(result.get('valid', False) for result in validation_results.values())
        
        # Collect errors
        errors = []
        for name, result in validation_results.items():
            if not result.get('valid', False):
                error_msg = result.get('error', f'{name} validation failed')
                errors.append(f"{name}: {error_msg}")
        
        # Calculate overall readiness score
        valid_count = sum(1 for result in validation_results.values() if result.get('valid', False))
        readiness_score = (valid_count / len(validation_results)) * 100
        
        final_result = {
            'overall_valid': overall_valid,
            'readiness_score': round(readiness_score, 1),
            'validation_results': validation_results,
            'errors': errors,
            'validated_at': time.time()
        }
        
        if not overall_valid:
            logger.warning(f"Validation failed for hearing {hearing_id}: {errors}")
        else:
            logger.info(f"Validation successful for hearing {hearing_id} (readiness: {readiness_score:.1f}%)")
        
        return final_result
    
    def get_recommendations(self, validation_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        if not validation_result['overall_valid']:
            recommendations.append("⚠️ Fix validation errors before proceeding with processing")
            
            for error in validation_result['errors']:
                if 'memory' in error.lower():
                    recommendations.append("💾 Free up system memory or close other applications")
                elif 'disk' in error.lower():
                    recommendations.append("💿 Free up disk space or move files to external storage")
                elif 'cpu' in error.lower():
                    recommendations.append("⚡ Wait for CPU usage to decrease or stop other processes")
                elif 'api' in error.lower():
                    recommendations.append("🔑 Check OpenAI API key configuration in Memex settings")
                elif 'audio' in error.lower():
                    recommendations.append("🎵 Check audio file format and integrity")
                elif 'metadata' in error.lower():
                    recommendations.append("📋 Verify hearing exists in database with complete metadata")
        
        # Performance recommendations
        if validation_result['readiness_score'] < 100:
            recommendations.append("🔧 Consider optimizing system resources for better performance")
        
        # Cost recommendations
        audio_validation = validation_result['validation_results'].get('audio_file', {})
        if audio_validation.get('valid') and 'processing_estimates' in audio_validation:
            estimates = audio_validation['processing_estimates']
            if estimates['estimated_cost_usd'] > 5.0:
                recommendations.append(f"💰 High processing cost estimated: ${estimates['estimated_cost_usd']:.2f}")
            if estimates['estimated_time_minutes'] > 60:
                recommendations.append(f"⏱️ Long processing time estimated: {estimates['estimated_time_minutes']:.1f} minutes")
        
        return recommendations

# Global validator instance
preprocessing_validator = PreprocessingValidator()

async def validate_before_processing(audio_path: str, hearing_id: int) -> Dict[str, Any]:
    """
    Validate all requirements before starting audio processing.
    
    Args:
        audio_path: Path to audio file
        hearing_id: Hearing ID for metadata validation
        
    Returns:
        Validation results with recommendations
        
    Raises:
        PreprocessingValidationError: If validation fails
    """
    result = await preprocessing_validator.validate_processing_readiness(audio_path, hearing_id)
    
    if not result['overall_valid']:
        raise PreprocessingValidationError(
            f"Pre-processing validation failed: {result['errors'][:3]}",  # First 3 errors
            result
        )
    
    return result

if __name__ == "__main__":
    async def test_validator():
        """Test the preprocessing validator."""
        validator = PreprocessingValidator()
        
        # Test with mock data
        try:
            result = await validator.validate_processing_readiness(
                "/nonexistent/file.wav", 
                999
            )
            print(f"Validation result: {result}")
            
            recommendations = validator.get_recommendations(result)
            print(f"Recommendations: {recommendations}")
            
        except Exception as e:
            print(f"Test error: {e}")
    
    # Uncomment to run test
    # asyncio.run(test_validator())