"""
Congressional metadata models for speaker identification and transcript enrichment.
"""

from .committee_member import CommitteeMember
from .hearing_witness import HearingWitness  
from .hearing import Hearing
from .metadata_loader import MetadataLoader

__all__ = [
    'CommitteeMember',
    'HearingWitness', 
    'Hearing',
    'MetadataLoader'
]