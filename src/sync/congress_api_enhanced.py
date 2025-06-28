"""
Enhanced Congress.gov API client for comprehensive hearing data collection.
Part of Phase 7A: Automated Data Synchronization
"""

import os
import requests
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from dataclasses import dataclass
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

@dataclass
class HearingRecord:
    """Structured hearing record from Congress API"""
    congress_api_id: str
    committee_code: str
    hearing_title: str
    hearing_date: str
    hearing_type: str
    meeting_status: str
    location_info: Dict[str, Any]
    documents: List[Dict[str, Any]]
    witnesses: List[Dict[str, Any]]
    raw_data: Dict[str, Any]

class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, calls: int = 10, period: int = 60):
        self.calls = calls
        self.period = period
        self.call_times = []
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()
        
        # Remove calls outside the current period
        self.call_times = [t for t in self.call_times if now - t < self.period]
        
        # If we're at the limit, wait
        if len(self.call_times) >= self.calls:
            sleep_time = self.period - (now - self.call_times[0]) + 0.1
            if sleep_time > 0:
                logger.info(f"Rate limit reached, waiting {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        self.call_times.append(now)

class CongressAPIEnhanced:
    """Enhanced Congress API client for comprehensive hearing data"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize enhanced Congress API client"""
        self.api_key = api_key or os.getenv('CONGRESS_API_KEY')
        if not self.api_key:
            raise ValueError("Congress API key required. Set CONGRESS_API_KEY environment variable.")
        
        self.base_url = "https://api.congress.gov/v3"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Senate-Hearing-Capture-Agent/1.0 (Educational Research)',
            'Accept': 'application/json'
        })
        self.rate_limiter = RateLimiter(calls=10, period=60)
        
        # Committee code mapping for standardization
        self.committee_codes = {
            'SCOM': 'commerce-science-and-transportation',
            'SSCI': 'intelligence', 
            'SBAN': 'banking-housing-and-urban-affairs',
            'SSJU': 'judiciary',
            'HJUD': 'house-judiciary',
            'SFRC': 'foreign-relations',
            'SASC': 'armed-services',
            'SHELP': 'health-education-labor-and-pensions'
        }
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make rate-limited API request with error handling"""
        
        self.rate_limiter.wait_if_needed()
        
        if params is None:
            params = {}
        
        params['api_key'] = self.api_key
        params['format'] = 'json'
        
        url = urljoin(self.base_url, endpoint)
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {endpoint}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from {endpoint}: {e}")
            return None
    
    def get_committee_meetings(self, committee_code: str, 
                              days_back: int = 30, days_forward: int = 30) -> List[HearingRecord]:
        """Get committee meetings with comprehensive metadata"""
        
        # Calculate date range
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=days_forward)).strftime('%Y-%m-%d')
        
        # Map internal committee code to API format
        api_committee_code = self.committee_codes.get(committee_code, committee_code.lower())
        
        logger.info(f"Fetching meetings for {committee_code} ({api_committee_code}) from {start_date} to {end_date}")
        
        # Get committee meetings
        endpoint = f"/committee/{api_committee_code}/meeting"
        params = {
            'fromDateTime': start_date,
            'toDateTime': end_date,
            'limit': 250  # Maximum allowed
        }
        
        response = self._make_request(endpoint, params)
        if not response:
            logger.warning(f"No response for committee {committee_code} meetings")
            return []
        
        meetings = response.get('meetings', [])
        logger.info(f"Found {len(meetings)} meetings for {committee_code}")
        
        # Process each meeting to extract hearing data
        hearing_records = []
        for meeting in meetings:
            try:
                hearing_record = self._process_meeting_data(meeting, committee_code)
                if hearing_record:
                    hearing_records.append(hearing_record)
            except Exception as e:
                logger.error(f"Error processing meeting {meeting.get('meetingId', 'unknown')}: {e}")
                continue
        
        return hearing_records
    
    def _process_meeting_data(self, meeting: Dict[str, Any], committee_code: str) -> Optional[HearingRecord]:
        """Process raw meeting data into structured hearing record"""
        
        try:
            # Extract basic meeting info
            meeting_id = meeting.get('meetingId', '')
            title = meeting.get('title', 'Untitled Meeting')
            date_str = meeting.get('date', '')
            
            # Parse date
            if date_str:
                try:
                    hearing_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
                except ValueError:
                    # Try alternative format
                    try:
                        hearing_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d')
                    except ValueError:
                        hearing_date = date_str
            else:
                hearing_date = datetime.now().strftime('%Y-%m-%d')
            
            # Extract meeting type and status
            meeting_type = meeting.get('meetingType', 'Hearing')
            status = meeting.get('status', 'Scheduled')
            
            # Extract location information
            location_info = {
                'room': meeting.get('room', ''),
                'building': meeting.get('building', ''),
                'address': meeting.get('address', ''),
                'description': meeting.get('location', '')
            }
            
            # Get detailed meeting information if available
            documents = self._extract_meeting_documents(meeting)
            witnesses = self._extract_meeting_witnesses(meeting)
            
            return HearingRecord(
                congress_api_id=meeting_id,
                committee_code=committee_code,
                hearing_title=title,
                hearing_date=hearing_date,
                hearing_type=meeting_type,
                meeting_status=status,
                location_info=location_info,
                documents=documents,
                witnesses=witnesses,
                raw_data=meeting
            )
        
        except Exception as e:
            logger.error(f"Error processing meeting data: {e}")
            return None
    
    def _extract_meeting_documents(self, meeting: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract document information from meeting data"""
        
        documents = []
        
        # Check for witness statements
        if 'witnesses' in meeting:
            for witness in meeting['witnesses']:
                if 'statement' in witness:
                    documents.append({
                        'type': 'witness_statement',
                        'title': f"Statement of {witness.get('name', 'Unknown')}",
                        'url': witness['statement'].get('url', ''),
                        'witness_name': witness.get('name', '')
                    })
        
        # Check for committee documents
        if 'documents' in meeting:
            for doc in meeting['documents']:
                documents.append({
                    'type': 'committee_document',
                    'title': doc.get('title', 'Untitled Document'),
                    'url': doc.get('url', ''),
                    'description': doc.get('description', '')
                })
        
        return documents
    
    def _extract_meeting_witnesses(self, meeting: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract witness information from meeting data"""
        
        witnesses = []
        
        if 'witnesses' in meeting:
            for witness in meeting['witnesses']:
                witness_info = {
                    'name': witness.get('name', ''),
                    'title': witness.get('title', ''),
                    'organization': witness.get('organization', ''),
                    'statement_url': '',
                    'biography': witness.get('biography', '')
                }
                
                # Extract statement URL if available
                if 'statement' in witness:
                    witness_info['statement_url'] = witness['statement'].get('url', '')
                
                witnesses.append(witness_info)
        
        return witnesses
    
    def get_recent_hearings_all_committees(self, days_back: int = 7) -> List[HearingRecord]:
        """Get recent hearings across all priority committees"""
        
        all_hearings = []
        
        for committee_code in self.committee_codes.keys():
            try:
                committee_hearings = self.get_committee_meetings(committee_code, days_back=days_back)
                all_hearings.extend(committee_hearings)
                
                # Small delay between committee requests
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to fetch hearings for {committee_code}: {e}")
                continue
        
        # Sort by date descending
        all_hearings.sort(key=lambda h: h.hearing_date, reverse=True)
        
        return all_hearings
    
    def validate_api_access(self) -> bool:
        """Validate API access and connectivity"""
        
        try:
            # Test with a simple committee request
            response = self._make_request("/committee", {'limit': 1})
            
            if response and 'committees' in response:
                logger.info("Congress API access validated successfully")
                return True
            else:
                logger.error("Invalid response from Congress API")
                return False
        
        except Exception as e:
            logger.error(f"Congress API validation failed: {e}")
            return False
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get API status and rate limit information"""
        
        status = {
            'api_accessible': False,
            'rate_limit_remaining': len(self.rate_limiter.call_times),
            'rate_limit_reset_time': None,
            'last_request_time': None
        }
        
        try:
            # Make a lightweight test request
            start_time = time.time()
            response = self._make_request("/committee", {'limit': 1})
            end_time = time.time()
            
            if response:
                status['api_accessible'] = True
                status['last_request_time'] = datetime.now().isoformat()
                status['response_time_ms'] = round((end_time - start_time) * 1000, 2)
            
        except Exception as e:
            status['error'] = str(e)
        
        return status

if __name__ == "__main__":
    # Test the enhanced API client
    import os
    from pathlib import Path
    
    # Test with environment variable or placeholder
    if os.getenv('CONGRESS_API_KEY'):
        api = CongressAPIEnhanced()
        
        # Validate access
        if api.validate_api_access():
            print("✓ API access validated")
            
            # Get recent hearings for one committee
            hearings = api.get_committee_meetings('SCOM', days_back=14)
            print(f"✓ Found {len(hearings)} recent hearings for Commerce Committee")
            
            if hearings:
                sample = hearings[0]
                print(f"Sample hearing: {sample.hearing_title}")
                print(f"Date: {sample.hearing_date}")
                print(f"Documents: {len(sample.documents)}")
                print(f"Witnesses: {len(sample.witnesses)}")
            
            # Check API status
            status = api.get_api_status()
            print(f"✓ API Status: {status}")
        
        else:
            print("✗ API access validation failed")
    else:
        print("Congress API key not found. Set CONGRESS_API_KEY environment variable for testing.")
        print("Enhanced Congress API client created successfully.")