#!/usr/bin/env python3
"""
Audio chunking system for Senate hearing audio processing.
Splits large audio files into API-compatible chunks with overlap for continuity.
"""

import os
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import tempfile
import shutil
import json
from datetime import datetime

from audio_analyzer import AudioAnalyzer, AudioAnalysis

# Import streaming processor for memory optimization
try:
    from streaming_audio_processor import (
        StreamingAudioProcessor,
        initialize_streaming_processor,
        shutdown_streaming_processor
    )
    STREAMING_AVAILABLE = True
except ImportError:
    STREAMING_AVAILABLE = False

@dataclass
class AudioChunk:
    """Container for audio chunk information."""
    chunk_index: int
    file_path: Path
    start_time: float
    end_time: float
    duration: float
    file_size_bytes: int
    file_size_mb: float
    overlap_start: float = 0.0  # Overlap with previous chunk
    overlap_end: float = 0.0    # Overlap with next chunk
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'chunk_index': self.chunk_index,
            'file_path': str(self.file_path),
            'start_time': round(self.start_time, 2),
            'end_time': round(self.end_time, 2),
            'duration': round(self.duration, 2),
            'file_size_bytes': self.file_size_bytes,
            'file_size_mb': round(self.file_size_mb, 2),
            'overlap_start': round(self.overlap_start, 2),
            'overlap_end': round(self.overlap_end, 2)
        }

@dataclass
class ChunkingResult:
    """Container for complete chunking operation results."""
    original_file: Path
    chunks: List[AudioChunk]
    total_chunks: int
    temp_directory: Path
    overlap_duration: float
    metadata_file: Path
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'original_file': str(self.original_file),
            'chunks': [chunk.to_dict() for chunk in self.chunks],
            'total_chunks': self.total_chunks,
            'temp_directory': str(self.temp_directory),
            'overlap_duration': self.overlap_duration,
            'metadata_file': str(self.metadata_file),
            'created_at': self.created_at
        }

class AudioChunker:
    """System for splitting large audio files into API-compatible chunks."""
    
    def __init__(self, temp_base_dir: Optional[Path] = None, use_streaming: bool = True):
        """Initialize the audio chunker."""
        self.analyzer = AudioAnalyzer()
        self.overlap_duration = 30.0  # 30 seconds overlap
        self.max_chunk_size_mb = 20.0  # Safe under 25MB API limit
        self.temp_base_dir = temp_base_dir or Path(__file__).parent / 'output' / 'temp_chunks'
        self.temp_base_dir.mkdir(parents=True, exist_ok=True)
        self.use_streaming = use_streaming and STREAMING_AVAILABLE
        self.streaming_processor = None
        
    async def chunk_audio_file_streaming(self, audio_file: Path, hearing_id: Optional[str] = None) -> ChunkingResult:
        """Split an audio file into chunks using streaming for memory optimization."""
        if not self.use_streaming:
            raise ValueError("Streaming not available, use chunk_audio_file() instead")
            
        # Initialize streaming processor if needed
        if not self.streaming_processor:
            self.streaming_processor = StreamingAudioProcessor()
            await self.streaming_processor.start()
        
        # Analyze the audio file first
        analysis = self.analyzer.analyze_file(audio_file)
        
        if not analysis.needs_chunking:
            raise ValueError(f"Audio file {audio_file.name} doesn't need chunking (size: {analysis.file_size_mb:.2f}MB)")
        
        print(f"🔧 Chunking audio file with streaming: {audio_file.name}")
        print(f"📊 File size: {analysis.file_size_mb:.2f}MB, Duration: {analysis.duration_minutes:.2f} minutes")
        print(f"📦 Will create {analysis.estimated_chunks} chunks with {self.overlap_duration}s overlap")
        
        # Create temporary directory for chunks
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hearing_prefix = hearing_id or "unknown"
        temp_dir = self.temp_base_dir / f"{hearing_prefix}_{timestamp}_streaming"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Calculate chunk parameters
            chunk_params = self._calculate_chunk_parameters(analysis)
            
            # Create chunk specifications for streaming
            chunk_specs = self._create_chunk_specifications(chunk_params)
            
            # Create chunks using streaming processor
            chunk_paths = await self.streaming_processor.create_chunks_streaming(
                str(audio_file), chunk_specs
            )
            
            # Create chunk objects from the created files
            chunks = self._create_chunk_objects_from_files(chunk_paths, chunk_specs, temp_dir)
            
            # Create metadata file
            metadata_file = temp_dir / "chunking_metadata.json"
            
            # Create result object
            result = ChunkingResult(
                original_file=audio_file,
                chunks=chunks,
                total_chunks=len(chunks),
                temp_directory=temp_dir,
                overlap_duration=self.overlap_duration,
                metadata_file=metadata_file,
                created_at=datetime.now().isoformat()
            )
            
            # Save metadata
            self._save_metadata(result)
            
            # Validate chunks
            if not self._validate_chunks(chunks):
                raise Exception("Chunk validation failed")
            
            print(f"✅ Successfully created {len(chunks)} chunks using streaming")
            return result
            
        except Exception as e:
            # Cleanup on error
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise
    
    def chunk_audio_file(self, audio_file: Path, hearing_id: Optional[str] = None) -> ChunkingResult:
        """Split an audio file into chunks suitable for API processing."""
        
        # Analyze the audio file first
        analysis = self.analyzer.analyze_file(audio_file)
        
        if not analysis.needs_chunking:
            raise ValueError(f"Audio file {audio_file.name} doesn't need chunking (size: {analysis.file_size_mb:.2f}MB)")
        
        print(f"🔧 Chunking audio file: {audio_file.name}")
        print(f"📊 File size: {analysis.file_size_mb:.2f}MB, Duration: {analysis.duration_minutes:.2f} minutes")
        print(f"📦 Will create {analysis.estimated_chunks} chunks with {self.overlap_duration}s overlap")
        
        # Create temporary directory for chunks
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hearing_prefix = hearing_id or "unknown"
        temp_dir = self.temp_base_dir / f"{hearing_prefix}_{timestamp}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Calculate chunk parameters
            chunk_params = self._calculate_chunk_parameters(analysis)
            
            # Create chunks
            chunks = self._create_chunks(audio_file, temp_dir, chunk_params)
            
            # Create metadata file
            metadata_file = temp_dir / "chunking_metadata.json"
            
            # Create result object
            result = ChunkingResult(
                original_file=audio_file,
                chunks=chunks,
                total_chunks=len(chunks),
                temp_directory=temp_dir,
                overlap_duration=self.overlap_duration,
                metadata_file=metadata_file,
                created_at=datetime.now().isoformat()
            )
            
            # Save metadata
            with open(metadata_file, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
            
            print(f"✅ Successfully created {len(chunks)} chunks in {temp_dir}")
            return result
            
        except Exception as e:
            # Clean up on failure
            print(f"❌ Chunking failed, cleaning up temporary directory: {temp_dir}")
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise e
    
    def _calculate_chunk_parameters(self, analysis: AudioAnalysis) -> Dict[str, Any]:
        """Calculate optimal chunk parameters based on audio analysis."""
        
        # Calculate target chunk duration in seconds
        total_duration = analysis.duration_seconds
        target_chunks = analysis.estimated_chunks
        
        # Account for overlap in duration calculation
        # Each chunk (except first and last) will have overlap on both sides
        effective_overlap_per_chunk = self.overlap_duration
        total_overlap_duration = (target_chunks - 1) * effective_overlap_per_chunk
        
        # Chunk duration without overlap
        base_chunk_duration = (total_duration - total_overlap_duration) / target_chunks
        
        # Actual chunk duration including overlap
        chunk_duration = base_chunk_duration + self.overlap_duration
        
        return {
            'target_chunks': target_chunks,
            'chunk_duration': chunk_duration,
            'base_chunk_duration': base_chunk_duration,
            'overlap_duration': self.overlap_duration,
            'total_duration': total_duration
        }
    
    def _create_chunks(self, audio_file: Path, temp_dir: Path, chunk_params: Dict[str, Any]) -> List[AudioChunk]:
        """Create audio chunks using ffmpeg."""
        chunks = []
        
        base_duration = chunk_params['base_chunk_duration']
        overlap = chunk_params['overlap_duration']
        total_duration = chunk_params['total_duration']
        
        current_start = 0.0
        chunk_index = 0
        
        while current_start < total_duration:
            # Calculate chunk end time
            chunk_end = min(current_start + base_duration + overlap, total_duration)
            
            # For the first chunk, no overlap at the beginning
            actual_start = current_start
            if chunk_index > 0:
                actual_start = max(0, current_start - overlap)
            
            # Calculate overlap information
            overlap_start = 0.0 if chunk_index == 0 else overlap
            overlap_end = 0.0 if chunk_end >= total_duration else overlap
            
            # Create chunk file
            chunk_filename = f"chunk_{chunk_index:03d}.mp3"
            chunk_path = temp_dir / chunk_filename
            
            # Extract chunk using ffmpeg
            self._extract_chunk(audio_file, chunk_path, actual_start, chunk_end - actual_start)
            
            # Get chunk file info
            chunk_size = chunk_path.stat().st_size
            chunk_size_mb = chunk_size / (1024 * 1024)
            
            # Create chunk object
            chunk = AudioChunk(
                chunk_index=chunk_index,
                file_path=chunk_path,
                start_time=actual_start,
                end_time=chunk_end,
                duration=chunk_end - actual_start,
                file_size_bytes=chunk_size,
                file_size_mb=chunk_size_mb,
                overlap_start=overlap_start,
                overlap_end=overlap_end
            )
            
            chunks.append(chunk)
            
            print(f"📦 Created chunk {chunk_index}: {chunk_size_mb:.2f}MB, "
                  f"{chunk.duration:.1f}s ({actual_start:.1f}s - {chunk_end:.1f}s)")
            
            # Move to next chunk
            current_start += base_duration
            chunk_index += 1
        
        return chunks
    
    def _extract_chunk(self, input_file: Path, output_file: Path, start_time: float, duration: float):
        """Extract a chunk from the audio file using ffmpeg."""
        cmd = [
            'ffmpeg',
            '-i', str(input_file),
            '-ss', str(start_time),
            '-t', str(duration),
            '-c', 'copy',  # Copy without re-encoding to preserve quality
            '-avoid_negative_ts', 'make_zero',
            '-y',  # Overwrite output file
            str(output_file)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg error creating chunk: {e}")
            print(f"FFmpeg stderr: {e.stderr}")
            raise Exception(f"Failed to create audio chunk: {e}")
    
    def cleanup_chunks(self, chunking_result: ChunkingResult):
        """Clean up temporary chunk files."""
        if chunking_result.temp_directory.exists():
            print(f"🧹 Cleaning up chunks in: {chunking_result.temp_directory}")
            shutil.rmtree(chunking_result.temp_directory)
            print(f"✅ Cleanup completed")
    
    def validate_chunks(self, chunking_result: ChunkingResult) -> bool:
        """Validate that all chunks were created successfully and are under size limit."""
        print(f"🔍 Validating {len(chunking_result.chunks)} chunks...")
        
        all_valid = True
        
        for chunk in chunking_result.chunks:
            # Check file exists
            if not chunk.file_path.exists():
                print(f"❌ Chunk {chunk.chunk_index} file missing: {chunk.file_path}")
                all_valid = False
                continue
            
            # Check file size
            if chunk.file_size_mb > self.max_chunk_size_mb:
                print(f"❌ Chunk {chunk.chunk_index} too large: {chunk.file_size_mb:.2f}MB > {self.max_chunk_size_mb}MB")
                all_valid = False
                continue
                
            # Check file is not empty
            if chunk.file_size_bytes == 0:
                print(f"❌ Chunk {chunk.chunk_index} is empty")
                all_valid = False
                continue
            
            print(f"✅ Chunk {chunk.chunk_index}: {chunk.file_size_mb:.2f}MB, {chunk.duration:.1f}s")
        
        if all_valid:
            print(f"✅ All {len(chunking_result.chunks)} chunks validated successfully")
        else:
            print(f"❌ Chunk validation failed")
            
        return all_valid
    
    def _create_chunk_specifications(self, chunk_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create chunk specifications for streaming processor."""
        specs = []
        
        base_duration = chunk_params['base_chunk_duration']
        overlap = chunk_params['overlap_duration']
        total_duration = chunk_params['total_duration']
        
        current_start = 0.0
        chunk_index = 0
        
        while current_start < total_duration:
            # Calculate chunk end time
            chunk_end = min(current_start + base_duration + overlap, total_duration)
            
            # For the first chunk, no overlap at the beginning
            actual_start = current_start
            if chunk_index > 0:
                actual_start = max(0, current_start - overlap)
            
            spec = {
                'chunk_index': chunk_index,
                'start_time': actual_start,
                'duration': chunk_end - actual_start,
                'end_time': chunk_end,
                'overlap_start': 0.0 if chunk_index == 0 else overlap,
                'overlap_end': 0.0 if chunk_end >= total_duration else overlap
            }
            
            specs.append(spec)
            
            # Move to next chunk start
            current_start += base_duration
            chunk_index += 1
            
        return specs
    
    def _create_chunk_objects_from_files(self, chunk_paths: List[str], 
                                       chunk_specs: List[Dict[str, Any]], 
                                       temp_dir: Path) -> List[AudioChunk]:
        """Create AudioChunk objects from streaming-created files."""
        chunks = []
        
        for chunk_path, spec in zip(chunk_paths, chunk_specs):
            chunk_path_obj = Path(chunk_path)
            
            # Get file info
            chunk_size = chunk_path_obj.stat().st_size
            chunk_size_mb = chunk_size / (1024 * 1024)
            
            # Create chunk object
            chunk = AudioChunk(
                chunk_index=spec['chunk_index'],
                file_path=chunk_path_obj,
                start_time=spec['start_time'],
                end_time=spec['end_time'],
                duration=spec['duration'],
                file_size_bytes=chunk_size,
                file_size_mb=chunk_size_mb,
                overlap_start=spec['overlap_start'],
                overlap_end=spec['overlap_end']
            )
            
            chunks.append(chunk)
            
        return chunks
    
    def _validate_chunks(self, chunks: List[AudioChunk]) -> bool:
        """Validate that chunks are properly created."""
        for chunk in chunks:
            # Check file exists and has content
            if not chunk.file_path.exists():
                print(f"❌ Chunk file not found: {chunk.file_path}")
                return False
                
            if chunk.file_size_bytes == 0:
                print(f"❌ Empty chunk file: {chunk.file_path}")
                return False
                
            # Check size limit
            if chunk.file_size_mb > self.max_chunk_size_mb:
                print(f"❌ Chunk too large: {chunk.file_path} ({chunk.file_size_mb:.2f}MB)")
                return False
                
        return True
    
    async def cleanup_streaming_processor(self):
        """Cleanup streaming processor resources."""
        if self.streaming_processor:
            await self.streaming_processor.stop()
            self.streaming_processor = None

def main():
    """Test the audio chunker with the real captured audio file."""
    chunker = AudioChunker()
    
    # Test with the real captured audio file
    audio_file = Path(__file__).parent / 'output' / 'real_audio' / 'senate_hearing_20250705_225321_stream1.mp3'
    
    if not audio_file.exists():
        print(f"❌ Audio file not found: {audio_file}")
        return False
    
    print(f"🎵 Testing audio chunking with: {audio_file.name}")
    
    try:
        # Create chunks
        result = chunker.chunk_audio_file(audio_file, hearing_id="test_hearing")
        
        # Validate chunks
        if chunker.validate_chunks(result):
            print(f"\n🎉 Chunking test successful!")
            print(f"📊 Summary:")
            print(f"   Original file: {result.original_file.name}")
            print(f"   Chunks created: {result.total_chunks}")
            print(f"   Temp directory: {result.temp_directory}")
            print(f"   Overlap duration: {result.overlap_duration}s")
            
            # Show chunk details
            print(f"\n📦 Chunk Details:")
            for chunk in result.chunks:
                print(f"   Chunk {chunk.chunk_index}: {chunk.file_size_mb:.2f}MB, "
                      f"{chunk.duration:.1f}s, {chunk.start_time:.1f}s-{chunk.end_time:.1f}s")
            
            # Clean up (comment out to keep chunks for testing)
            # chunker.cleanup_chunks(result)
            print(f"\n💡 Chunks preserved at: {result.temp_directory}")
            print(f"💡 Run cleanup manually or proceed to transcription testing")
            
            return True
        else:
            print(f"❌ Chunk validation failed")
            return False
            
    except Exception as e:
        print(f"❌ Chunking test failed: {e}")
        return False

if __name__ == "__main__":
    main()