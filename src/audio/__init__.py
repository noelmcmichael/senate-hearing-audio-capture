"""
Audio processing module for Senate Hearing Audio Capture
"""

from .trimming import AudioTrimmer, get_audio_trimmer

__all__ = ['AudioTrimmer', 'get_audio_trimmer']