"""
Congress.gov API client for official congressional data.

Provides secure access to the official Congress.gov API for member, committee,
and hearing data with proper authentication and rate limiting.
"""

import requests
import time
import keyring
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime


@dataclass
class APIResponse:
    """Standardized API response wrapper."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    rate_limit_remaining: Optional[int] = None


class CongressAPIClient:
    """
    Client for the official Congress.gov API.
    
    Provides authenticated access to congressional data including members,
    committees, hearings, and other congressional information.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Congress API client.
        
        Args:
            api_key: Optional API key. If not provided, will try to retrieve from keyring.
        """
        self.base_url = "https://api.congress.gov/v3"
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
        
        # Get API key
        if api_key:
            self.api_key = api_key
        else:
            try:
                self.api_key = keyring.get_password('memex', 'CONGRESS_API_KEY')
                if not self.api_key:
                    raise ValueError("No Congress API key found in keyring. Please set CONGRESS_API_KEY.")
            except Exception as e:
                raise ValueError(f"Failed to retrieve Congress API key: {e}")
        
        # Set up session headers
        self.session.headers.update({
            'User-Agent': 'Senate-Hearing-Audio-Capture/1.0 (https://github.com/user/repo)',
            'Accept': 'application/json'
        })
        
        # Rate limiting (5,000 requests per hour = ~1.4 requests per second)
        self.rate_limit_delay = 0.75  # Conservative 750ms between requests
        self.last_request_time = 0
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> APIResponse:
        """
        Make authenticated request to Congress API.
        
        Args:
            endpoint: API endpoint path
            params: Optional query parameters
            
        Returns:
            APIResponse with result data or error information
        """
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        
        # Prepare request
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_params = {'api_key': self.api_key}
        if params:
            request_params.update(params)
        
        try:
            self.logger.debug(f"Congress API request: {url}")
            response = self.session.get(url, params=request_params, timeout=30)
            self.last_request_time = time.time()
            
            # Extract rate limit info
            rate_limit_remaining = response.headers.get('X-RateLimit-Remaining')
            if rate_limit_remaining:
                rate_limit_remaining = int(rate_limit_remaining)
            
            if response.status_code == 200:
                data = response.json()
                return APIResponse(
                    success=True,
                    data=data,
                    status_code=response.status_code,
                    rate_limit_remaining=rate_limit_remaining
                )
            else:
                error_msg = f"API request failed: {response.status_code}"
                if response.text:
                    error_msg += f" - {response.text}"
                
                self.logger.warning(error_msg)
                return APIResponse(
                    success=False,
                    error=error_msg,
                    status_code=response.status_code,
                    rate_limit_remaining=rate_limit_remaining
                )
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {e}"
            self.logger.error(error_msg)
            return APIResponse(success=False, error=error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            self.logger.error(error_msg)
            return APIResponse(success=False, error=error_msg)
    
    def get_current_members(self, chamber: Optional[str] = None, limit: int = 250) -> APIResponse:
        """
        Get current members of Congress.
        
        Args:
            chamber: Optional chamber filter ('house' or 'senate')
            limit: Number of results to return (max 250)
            
        Returns:
            APIResponse containing member data
        """
        params = {
            'currentMember': 'true',
            'limit': min(limit, 250)
        }
        
        if chamber:
            endpoint = f"member/{chamber.lower()}"
        else:
            endpoint = "member"
        
        return self._make_request(endpoint, params)
    
    def get_member_details(self, bioguide_id: str) -> APIResponse:
        """
        Get detailed information for a specific member.
        
        Args:
            bioguide_id: Member's bioguide ID (e.g., 'C000127' for Cantwell)
            
        Returns:
            APIResponse containing detailed member information
        """
        endpoint = f"member/{bioguide_id}"
        return self._make_request(endpoint)
    
    def get_committees(self, congress: Optional[int] = None, chamber: Optional[str] = None) -> APIResponse:
        """
        Get committee information.
        
        Args:
            congress: Optional congress number (defaults to current)
            chamber: Optional chamber filter ('house', 'senate', or 'joint')
            
        Returns:
            APIResponse containing committee data
        """
        if congress and chamber:
            endpoint = f"committee/{congress}/{chamber.lower()}"
        elif congress:
            endpoint = f"committee/{congress}"
        else:
            endpoint = "committee"
        
        return self._make_request(endpoint)
    
    def get_committee_details(self, chamber: str, system_code: str) -> APIResponse:
        """
        Get detailed information for a specific committee.
        
        Args:
            chamber: Committee chamber ('house', 'senate', or 'joint')
            system_code: Committee system code (e.g., 'sscm00' for Senate Commerce)
            
        Returns:
            APIResponse containing detailed committee information
        """
        endpoint = f"committee/{chamber.lower()}/{system_code}"
        return self._make_request(endpoint)
    
    def get_current_congress(self) -> APIResponse:
        """
        Get information about the current congress.
        
        Returns:
            APIResponse containing current congress information
        """
        endpoint = "congress"
        params = {'limit': 1}
        return self._make_request(endpoint, params)
    
    def search_members_by_state(self, state_code: str, congress: Optional[int] = None) -> APIResponse:
        """
        Get members by state.
        
        Args:
            state_code: Two-letter state code (e.g., 'WA', 'TX')
            congress: Optional congress number (defaults to current)
            
        Returns:
            APIResponse containing members from the state
        """
        if not congress:
            congress_response = self.get_current_congress()
            if not congress_response.success:
                return congress_response
            congresses = congress_response.data.get('congresses', [])
            if not congresses:
                return APIResponse(success=False, error="No congress data found")
            try:
                congress = int(congresses[0].get('name', '').split('th')[0])
            except (ValueError, IndexError):
                return APIResponse(success=False, error="Could not parse congress number")
        
        endpoint = f"member/congress/{congress}/{state_code.upper()}"
        params = {'currentMember': 'true', 'limit': 250}
        return self._make_request(endpoint, params)
    
    def get_committee_members(self, chamber: str, system_code: str) -> APIResponse:
        """
        Get members of a specific committee.
        
        Note: This requires parsing committee details as the API doesn't have 
        a direct committee members endpoint.
        
        Args:
            chamber: Committee chamber
            system_code: Committee system code
            
        Returns:
            APIResponse containing committee information (members in history)
        """
        return self.get_committee_details(chamber, system_code)
    
    def get_hearings(self, congress: Optional[int] = None, limit: int = 250) -> APIResponse:
        """
        Get hearing information.
        
        Args:
            congress: Optional congress number
            limit: Number of results to return
            
        Returns:
            APIResponse containing hearing data
        """
        if congress:
            endpoint = f"hearing/{congress}"
        else:
            endpoint = "hearing"
        
        params = {'limit': min(limit, 250)}
        return self._make_request(endpoint, params)
    
    def test_connection(self) -> APIResponse:
        """
        Test API connection and authentication.
        
        Returns:
            APIResponse indicating connection status
        """
        self.logger.info("Testing Congress API connection...")
        response = self.get_current_congress()
        
        if response.success:
            congress_num = response.data.get('congress', {}).get('number', 'Unknown')
            self.logger.info(f"✅ Congress API connection successful. Current congress: {congress_num}")
        else:
            self.logger.error(f"❌ Congress API connection failed: {response.error}")
        
        return response
    
    def get_comprehensive_member_data(self, bioguide_id: str) -> Dict[str, Any]:
        """
        Get comprehensive member data combining multiple API calls.
        
        Args:
            bioguide_id: Member's bioguide ID
            
        Returns:
            Combined member data or None if failed
        """
        # Get basic member details
        member_response = self.get_member_details(bioguide_id)
        if not member_response.success:
            self.logger.error(f"Failed to get member details for {bioguide_id}: {member_response.error}")
            return None
        
        member_data = member_response.data.get('member', {})
        
        # Extract current service information
        current_term = None
        terms_data = member_data.get('terms', {})
        if isinstance(terms_data, dict):
            terms = terms_data.get('item', [])
        else:
            terms = terms_data if isinstance(terms_data, list) else []
            
        if terms:
            # Get most recent term
            current_term = terms[-1] if isinstance(terms, list) else terms
        
        return {
            'bioguide_id': member_data.get('bioguideId'),
            'name': {
                'first': member_data.get('firstName'),
                'middle': member_data.get('middleName'),
                'last': member_data.get('lastName'),
                'full': member_data.get('directOrderName'),
                'inverted': member_data.get('invertedOrderName'),
                'honorific': member_data.get('honorificName'),
                'suffix': member_data.get('suffixName')
            },
            'current_service': {
                'chamber': current_term.get('chamber') if current_term else None,
                'state_code': current_term.get('stateCode') if current_term else None,
                'state_name': current_term.get('stateName') if current_term else None,
                'district': current_term.get('district') if current_term else None,
                'party_name': current_term.get('partyName') if current_term else None,
                'party_code': current_term.get('partyCode') if current_term else None,
                'member_type': current_term.get('memberType') if current_term else None
            },
            'contact': {
                'office_address': member_data.get('addressInformation', {}).get('officeAddress'),
                'phone': member_data.get('addressInformation', {}).get('phoneNumber'),
                'official_url': member_data.get('officialUrl')
            },
            'biographical': {
                'birth_year': member_data.get('birthYear'),
                'death_year': member_data.get('deathYear'),
                'current_member': member_data.get('currentMember')
            },
            'api_metadata': {
                'update_date': member_data.get('updateDate'),
                'api_url': f"https://api.congress.gov/v3/member/{bioguide_id}"
            }
        }