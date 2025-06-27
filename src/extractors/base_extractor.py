"""Base class for stream extractors."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class StreamInfo:
    """Information about a discovered stream."""
    url: str
    format_type: str  # 'hls', 'mp4', 'youtube', etc.
    quality: Optional[str] = None
    duration: Optional[int] = None  # seconds
    title: Optional[str] = None
    metadata: Optional[Dict] = None


class BaseExtractor(ABC):
    """Base class for all stream extractors."""
    
    @abstractmethod
    def can_extract(self, url: str) -> bool:
        """Check if this extractor can handle the given URL.
        
        Args:
            url: The webpage URL to check
            
        Returns:
            True if this extractor can handle the URL
        """
        pass
    
    @abstractmethod
    def extract_streams(self, url: str) -> List[StreamInfo]:
        """Extract stream information from the given URL.
        
        Args:
            url: The webpage URL to extract from
            
        Returns:
            List of discovered streams
        """
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """Get the priority of this extractor (lower = higher priority).
        
        Returns:
            Priority value (0-100, where 0 is highest priority)
        """
        pass