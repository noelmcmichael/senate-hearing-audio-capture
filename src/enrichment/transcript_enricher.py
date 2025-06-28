"""
Transcript enricher for congressional hearing metadata integration.

Provides speaker identification and metadata annotation for transcripts.
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from models.metadata_loader import MetadataLoader
from models.committee_member import CommitteeMember
from models.hearing_witness import HearingWitness
from models.hearing import Hearing


class TranscriptEnricher:
    """
    Enriches transcripts with congressional metadata for improved analysis.
    
    Provides speaker identification, role annotation, and contextual metadata
    for congressional hearing transcripts.
    """
    
    def __init__(self, metadata_loader: Optional[MetadataLoader] = None):
        """
        Initialize transcript enricher.
        
        Args:
            metadata_loader: Optional metadata loader instance
        """
        self.metadata_loader = metadata_loader or MetadataLoader()
        self.logger = logging.getLogger(__name__)
        
        # Common speaking patterns in congressional hearings
        self.speaker_patterns = [
            r"^(Chair|Chairman|Chairwoman)\s+(.*?):",
            r"^(Ranking Member)\s+(.*?):",
            r"^(Senator|Sen\.)\s+(.*?):",
            r"^(Representative|Rep\.)\s+(.*?):",
            r"^(Mr\.|Ms\.|Mrs\.)\s+(.*?):",
            r"^(Dr\.)\s+(.*?):",
            r"^(Commissioner)\s+(.*?):",
            r"^(Professor)\s+(.*?):",
            r"^(.*?):\s*",  # Fallback pattern
        ]
    
    def identify_speaker(self, speaker_text: str, hearing_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Identify a speaker from transcript text.
        
        Args:
            speaker_text: Raw speaker text from transcript
            hearing_id: Optional hearing ID for context
            
        Returns:
            Dictionary with speaker information or None if not found
        """
        # Clean the speaker text
        clean_text = speaker_text.strip().rstrip(':').strip()
        
        # Try to find the speaker
        speaker = self.metadata_loader.find_speaker_by_name(clean_text, hearing_id)
        
        if speaker:
            if isinstance(speaker, CommitteeMember):
                return {
                    'speaker_id': speaker.member_id,
                    'speaker_type': 'member',
                    'full_name': speaker.full_name,
                    'display_name': speaker.get_display_name(),
                    'title': speaker.title,
                    'party': speaker.party,
                    'state': speaker.state,
                    'chamber': speaker.chamber,
                    'committee': speaker.committee,
                    'role': speaker.role
                }
            elif isinstance(speaker, HearingWitness):
                return {
                    'speaker_id': speaker.witness_id,
                    'speaker_type': 'witness',
                    'full_name': speaker.full_name,
                    'display_name': speaker.get_display_name(),
                    'title': speaker.title,
                    'organization': speaker.organization
                }
        
        # Return raw text if no match found
        return {
            'speaker_id': None,
            'speaker_type': 'unknown',
            'full_name': clean_text,
            'display_name': clean_text,
            'raw_text': speaker_text
        }
    
    def parse_transcript_line(self, line: str, hearing_id: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Parse a single transcript line for speaker and content.
        
        Args:
            line: Raw transcript line
            hearing_id: Optional hearing ID for context
            
        Returns:
            Tuple of (speaker_info, content) or (None, line) if no speaker found
        """
        line = line.strip()
        if not line:
            return None, ""
        
        # Try each speaker pattern
        for pattern in self.speaker_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                # Extract speaker and content
                if len(match.groups()) >= 2:
                    # Pattern with title and name
                    title = match.group(1)
                    name = match.group(2)
                    speaker_text = f"{title} {name}"
                    content = line[match.end():].strip()
                elif len(match.groups()) == 1:
                    # Pattern with just name
                    speaker_text = match.group(1)
                    content = line[match.end():].strip()
                else:
                    # Fallback pattern
                    speaker_text = match.group(0).rstrip(':')
                    content = line[match.end():].strip()
                
                speaker_info = self.identify_speaker(speaker_text, hearing_id)
                return speaker_info, content
        
        # No speaker pattern found
        return None, line
    
    def enrich_transcript(self, transcript_text: str, hearing_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Enrich a complete transcript with metadata.
        
        Args:
            transcript_text: Raw transcript text
            hearing_id: Optional hearing ID for context
            
        Returns:
            Enriched transcript with speaker metadata
        """
        lines = transcript_text.split('\n')
        enriched_segments = []
        current_speaker = None
        current_content = []
        
        for line_num, line in enumerate(lines, 1):
            speaker_info, content = self.parse_transcript_line(line, hearing_id)
            
            if speaker_info:
                # Save previous segment if exists
                if current_speaker and current_content:
                    enriched_segments.append({
                        'speaker': current_speaker,
                        'content': ' '.join(current_content).strip(),
                        'line_start': current_line_start,
                        'line_end': line_num - 1
                    })
                
                # Start new segment
                current_speaker = speaker_info
                current_content = [content] if content else []
                current_line_start = line_num
            elif current_speaker:
                # Continue current segment
                if line.strip():
                    current_content.append(line.strip())
            else:
                # No speaker context, treat as metadata or intro
                if line.strip():
                    enriched_segments.append({
                        'speaker': None,
                        'content': line.strip(),
                        'line_start': line_num,
                        'line_end': line_num,
                        'type': 'metadata'
                    })
        
        # Save final segment
        if current_speaker and current_content:
            enriched_segments.append({
                'speaker': current_speaker,
                'content': ' '.join(current_content).strip(),
                'line_start': current_line_start,
                'line_end': len(lines)
            })
        
        # Generate summary statistics
        speaker_stats = {}
        for segment in enriched_segments:
            if segment.get('speaker') and segment['speaker'].get('speaker_id'):
                speaker_id = segment['speaker']['speaker_id']
                if speaker_id not in speaker_stats:
                    speaker_stats[speaker_id] = {
                        'speaker_info': segment['speaker'],
                        'segment_count': 0,
                        'total_words': 0
                    }
                speaker_stats[speaker_id]['segment_count'] += 1
                speaker_stats[speaker_id]['total_words'] += len(segment['content'].split())
        
        return {
            'hearing_id': hearing_id,
            'segments': enriched_segments,
            'speaker_statistics': speaker_stats,
            'total_segments': len(enriched_segments),
            'identified_speakers': len(speaker_stats),
            'processing_metadata': {
                'enricher_version': '1.0',
                'total_lines': len(lines)
            }
        }
    
    def enrich_transcript_file(self, transcript_path: str, output_path: str, hearing_id: Optional[str] = None) -> None:
        """
        Enrich a transcript file and save enriched version.
        
        Args:
            transcript_path: Path to raw transcript file
            output_path: Path to save enriched transcript
            hearing_id: Optional hearing ID for context
        """
        try:
            # Read transcript
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript_text = f.read()
            
            # Enrich transcript
            enriched = self.enrich_transcript(transcript_text, hearing_id)
            
            # Save enriched version
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(enriched, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Enriched transcript saved: {output_path}")
            self.logger.info(f"Identified {enriched['identified_speakers']} speakers in {enriched['total_segments']} segments")
            
        except Exception as e:
            self.logger.error(f"Error enriching transcript: {e}")
            raise
    
    def generate_speaker_summary(self, enriched_transcript: Dict[str, Any]) -> str:
        """
        Generate a summary of speakers in the enriched transcript.
        
        Args:
            enriched_transcript: Enriched transcript data
            
        Returns:
            Formatted speaker summary
        """
        speaker_stats = enriched_transcript.get('speaker_statistics', {})
        
        if not speaker_stats:
            return "No identified speakers found in transcript."
        
        summary_lines = ["Speaker Summary:", "=" * 50]
        
        # Sort by total words (most active speakers first)
        sorted_speakers = sorted(
            speaker_stats.items(),
            key=lambda x: x[1]['total_words'],
            reverse=True
        )
        
        for speaker_id, stats in sorted_speakers:
            speaker_info = stats['speaker_info']
            summary_lines.append(
                f"{speaker_info['display_name']}: "
                f"{stats['segment_count']} segments, "
                f"{stats['total_words']} words"
            )
        
        summary_lines.append("")
        summary_lines.append(f"Total: {len(speaker_stats)} identified speakers")
        
        return "\n".join(summary_lines)