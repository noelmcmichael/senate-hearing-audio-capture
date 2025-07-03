#!/usr/bin/env python3
"""
Committee Structure Discovery System
Discovers all Senate committees and subcommittees with metadata
"""

import json
import requests
from pathlib import Path
from typing import Dict, List, Optional, Set
import time
from datetime import datetime
import logging
from dataclasses import dataclass, asdict
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Committee:
    """Committee data structure"""
    code: str
    name: str
    full_name: str
    chamber: str
    type: str  # "committee" or "subcommittee"
    parent_code: Optional[str] = None
    website_url: Optional[str] = None
    isvp_compatible: Optional[bool] = None
    member_count: Optional[int] = None
    chair: Optional[str] = None
    ranking_member: Optional[str] = None
    jurisdiction: Optional[str] = None
    subcommittees: Optional[List[str]] = None
    api_source: Optional[str] = None
    discovery_date: Optional[str] = None

class CommitteeDiscovery:
    """Senate Committee Discovery System"""
    
    def __init__(self, output_dir: str = "data/committees"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Senate committee base URLs
        self.senate_committees_url = "https://www.senate.gov/committees/"
        self.congress_api_base = "https://api.congress.gov/v3"
        
        # Known ISVP-compatible committees from previous work
        self.known_isvp_committees = {
            "SCOM": "Commerce, Science, and Transportation",
            "SSCI": "Intelligence", 
            "SBAN": "Banking, Housing, and Urban Affairs",
            "SSJU": "Judiciary"
        }
        
        self.discovered_committees: Dict[str, Committee] = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Senate Hearing Audio Capture System (Research/Academic)'
        })
        
    def discover_from_congress_api(self) -> Dict[str, Committee]:
        """Discover committees from Congress.gov API"""
        logger.info("Discovering committees from Congress.gov API...")
        
        try:
            # Get current Congress number (119th Congress)
            congress_num = 119
            url = f"{self.congress_api_base}/committee/{congress_num}/senate"
            
            # Note: In real implementation, we'd need API key
            # For now, we'll use the known structure and supplement with web scraping
            logger.info(f"Congress API URL: {url}")
            logger.info("Note: API key required for full access - using web scraping fallback")
            
            # Return empty dict to trigger web scraping
            return {}
            
        except Exception as e:
            logger.warning(f"Congress API access failed: {e}")
            return {}
    
    def discover_from_senate_website(self) -> Dict[str, Committee]:
        """Discover committees from Senate.gov website"""
        logger.info("Discovering committees from Senate.gov website...")
        
        try:
            response = self.session.get(self.senate_committees_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            committees = {}
            
            # Find standing committees section
            standing_committees = self._extract_standing_committees(soup)
            committees.update(standing_committees)
            
            # Find select committees 
            select_committees = self._extract_select_committees(soup)
            committees.update(select_committees)
            
            # Find joint committees
            joint_committees = self._extract_joint_committees(soup)
            committees.update(joint_committees)
            
            logger.info(f"Discovered {len(committees)} committees from Senate website")
            return committees
            
        except Exception as e:
            logger.error(f"Failed to discover from Senate website: {e}")
            return {}
    
    def _extract_standing_committees(self, soup: BeautifulSoup) -> Dict[str, Committee]:
        """Extract standing committees from Senate.gov"""
        committees = {}
        
        # Look for standing committees section
        standing_section = soup.find('section', {'id': 'standing-committees'}) or \
                          soup.find('div', {'class': 'standing-committees'}) or \
                          soup.find('h2', string=re.compile(r'Standing Committees', re.I))
        
        if standing_section:
            # Find committee links
            committee_links = standing_section.find_all('a', href=True)
            
            for link in committee_links:
                href = link.get('href')
                if href and 'committee' in href.lower():
                    committee_name = link.get_text(strip=True)
                    if committee_name and len(committee_name) > 3:
                        code = self._generate_committee_code(committee_name)
                        
                        committee = Committee(
                            code=code,
                            name=committee_name,
                            full_name=committee_name,
                            chamber="Senate",
                            type="committee",
                            website_url=urljoin(self.senate_committees_url, href),
                            isvp_compatible=code in self.known_isvp_committees,
                            api_source="Senate.gov website",
                            discovery_date=datetime.now().isoformat()
                        )
                        
                        committees[code] = committee
        
        # If no structured extraction, try alternative approach
        if not committees:
            committees = self._extract_committees_alternative(soup)
            
        return committees
    
    def _extract_select_committees(self, soup: BeautifulSoup) -> Dict[str, Committee]:
        """Extract select committees"""
        committees = {}
        
        # Look for select committees section
        select_section = soup.find('section', {'id': 'select-committees'}) or \
                        soup.find('div', {'class': 'select-committees'}) or \
                        soup.find('h2', string=re.compile(r'Select Committees', re.I))
        
        if select_section:
            committee_links = select_section.find_all('a', href=True)
            
            for link in committee_links:
                href = link.get('href')
                if href and 'committee' in href.lower():
                    committee_name = link.get_text(strip=True)
                    if committee_name and len(committee_name) > 3:
                        code = self._generate_committee_code(committee_name, prefix="SS")
                        
                        committee = Committee(
                            code=code,
                            name=committee_name,
                            full_name=committee_name,
                            chamber="Senate",
                            type="select",
                            website_url=urljoin(self.senate_committees_url, href),
                            api_source="Senate.gov website",
                            discovery_date=datetime.now().isoformat()
                        )
                        
                        committees[code] = committee
        
        return committees
    
    def _extract_joint_committees(self, soup: BeautifulSoup) -> Dict[str, Committee]:
        """Extract joint committees"""
        committees = {}
        
        # Look for joint committees section
        joint_section = soup.find('section', {'id': 'joint-committees'}) or \
                       soup.find('div', {'class': 'joint-committees'}) or \
                       soup.find('h2', string=re.compile(r'Joint Committees', re.I))
        
        if joint_section:
            committee_links = joint_section.find_all('a', href=True)
            
            for link in committee_links:
                href = link.get('href')
                if href and 'committee' in href.lower():
                    committee_name = link.get_text(strip=True)
                    if committee_name and len(committee_name) > 3:
                        code = self._generate_committee_code(committee_name, prefix="JC")
                        
                        committee = Committee(
                            code=code,
                            name=committee_name,
                            full_name=committee_name,
                            chamber="Joint",
                            type="joint",
                            website_url=urljoin(self.senate_committees_url, href),
                            api_source="Senate.gov website",
                            discovery_date=datetime.now().isoformat()
                        )
                        
                        committees[code] = committee
        
        return committees
    
    def _extract_committees_alternative(self, soup: BeautifulSoup) -> Dict[str, Committee]:
        """Alternative committee extraction method"""
        committees = {}
        
        # Look for all committee links
        all_links = soup.find_all('a', href=True)
        committee_links = [link for link in all_links 
                          if 'committee' in link.get('href', '').lower() and 
                          link.get_text(strip=True) and 
                          len(link.get_text(strip=True)) > 10]
        
        for link in committee_links:
            href = link.get('href')
            committee_name = link.get_text(strip=True)
            
            # Clean up committee name
            committee_name = re.sub(r'Committee on ', '', committee_name)
            committee_name = re.sub(r'Senate ', '', committee_name)
            
            if committee_name and len(committee_name) > 3:
                code = self._generate_committee_code(committee_name)
                
                committee = Committee(
                    code=code,
                    name=committee_name,
                    full_name=committee_name,
                    chamber="Senate",
                    type="committee",
                    website_url=urljoin(self.senate_committees_url, href),
                    isvp_compatible=code in self.known_isvp_committees,
                    api_source="Senate.gov website (alternative)",
                    discovery_date=datetime.now().isoformat()
                )
                
                committees[code] = committee
        
        return committees
    
    def _generate_committee_code(self, name: str, prefix: str = "S") -> str:
        """Generate committee code from name"""
        # Remove common words
        name = re.sub(r'\b(Committee|on|the|and|&|of|for|in|to)\b', '', name, flags=re.I)
        
        # Extract key words
        words = [word.strip() for word in name.split() if len(word.strip()) > 2]
        
        # Create code
        if len(words) >= 2:
            code = prefix + words[0][:2].upper() + words[1][:2].upper()
        elif len(words) == 1:
            code = prefix + words[0][:4].upper()
        else:
            code = prefix + "UNK"
        
        return code
    
    def discover_committee_subcommittees(self, committee: Committee) -> List[Committee]:
        """Discover subcommittees for a given committee"""
        logger.info(f"Discovering subcommittees for {committee.name}")
        
        subcommittees = []
        
        if not committee.website_url:
            return subcommittees
        
        try:
            response = self.session.get(committee.website_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for subcommittee links
            subcommittee_links = soup.find_all('a', href=True)
            
            for link in subcommittee_links:
                href = link.get('href')
                text = link.get_text(strip=True)
                
                if ('subcommittee' in text.lower() or 'subcommittee' in href.lower()) and \
                   len(text) > 5:
                    
                    subcommittee_code = committee.code + "_" + self._generate_subcommittee_code(text)
                    
                    subcommittee = Committee(
                        code=subcommittee_code,
                        name=text,
                        full_name=text,
                        chamber="Senate",
                        type="subcommittee",
                        parent_code=committee.code,
                        website_url=urljoin(committee.website_url, href),
                        api_source="Committee website",
                        discovery_date=datetime.now().isoformat()
                    )
                    
                    subcommittees.append(subcommittee)
            
            logger.info(f"Found {len(subcommittees)} subcommittees for {committee.name}")
            
        except Exception as e:
            logger.warning(f"Failed to discover subcommittees for {committee.name}: {e}")
        
        return subcommittees
    
    def _generate_subcommittee_code(self, name: str) -> str:
        """Generate subcommittee code"""
        # Remove "Subcommittee" and common words
        name = re.sub(r'\b(Subcommittee|on|the|and|&|of|for|in|to)\b', '', name, flags=re.I)
        
        words = [word.strip() for word in name.split() if len(word.strip()) > 2]
        
        if len(words) >= 2:
            return words[0][:2].upper() + words[1][:2].upper()
        elif len(words) == 1:
            return words[0][:4].upper()
        else:
            return "SUB"
    
    def discover_all_committees(self) -> Dict[str, Committee]:
        """Discover all committees from all sources"""
        logger.info("Starting comprehensive committee discovery...")
        
        all_committees = {}
        
        # Try Congress API first
        api_committees = self.discover_from_congress_api()
        all_committees.update(api_committees)
        
        # Supplement with Senate website
        website_committees = self.discover_from_senate_website()
        all_committees.update(website_committees)
        
        # Add known ISVP committees if missing
        all_committees.update(self._add_known_committees())
        
        # Discover subcommittees
        for committee in list(all_committees.values()):
            if committee.type == "committee":
                subcommittees = self.discover_committee_subcommittees(committee)
                for sub in subcommittees:
                    all_committees[sub.code] = sub
                
                # Update parent committee with subcommittee list
                if subcommittees:
                    committee.subcommittees = [sub.code for sub in subcommittees]
        
        self.discovered_committees = all_committees
        logger.info(f"Total committees discovered: {len(all_committees)}")
        
        return all_committees
    
    def _add_known_committees(self) -> Dict[str, Committee]:
        """Add known ISVP-compatible committees"""
        known_committees = {}
        
        committee_details = {
            "SCOM": {
                "name": "Commerce, Science, and Transportation",
                "website_url": "https://www.commerce.senate.gov/",
                "jurisdiction": "Interstate commerce, transportation, telecommunications"
            },
            "SSCI": {
                "name": "Intelligence",
                "website_url": "https://www.intelligence.senate.gov/",
                "jurisdiction": "Intelligence activities and programs"
            },
            "SBAN": {
                "name": "Banking, Housing, and Urban Affairs", 
                "website_url": "https://www.banking.senate.gov/",
                "jurisdiction": "Banking, housing, urban development"
            },
            "SSJU": {
                "name": "Judiciary",
                "website_url": "https://www.judiciary.senate.gov/",
                "jurisdiction": "Federal courts, constitutional law"
            }
        }
        
        for code, details in committee_details.items():
            committee = Committee(
                code=code,
                name=details["name"],
                full_name=f"Senate Committee on {details['name']}",
                chamber="Senate",
                type="committee",
                website_url=details["website_url"],
                isvp_compatible=True,
                jurisdiction=details["jurisdiction"],
                api_source="Known ISVP-compatible (validated)",
                discovery_date=datetime.now().isoformat()
            )
            
            known_committees[code] = committee
        
        return known_committees
    
    def save_committee_structure(self, output_file: str = "committee_structure.json"):
        """Save discovered committee structure"""
        output_path = self.output_dir / output_file
        
        # Convert to serializable format
        committee_data = {
            "discovery_info": {
                "discovery_date": datetime.now().isoformat(),
                "total_committees": len(self.discovered_committees),
                "sources": ["Congress.gov API", "Senate.gov website", "Known ISVP committees"],
                "isvp_compatible_count": len([c for c in self.discovered_committees.values() 
                                            if c.isvp_compatible])
            },
            "committees": {code: asdict(committee) for code, committee in self.discovered_committees.items()}
        }
        
        with open(output_path, 'w') as f:
            json.dump(committee_data, f, indent=2)
        
        logger.info(f"Committee structure saved to {output_path}")
        return output_path
    
    def generate_committee_summary(self):
        """Generate summary of discovered committees"""
        committees = self.discovered_committees
        
        summary = {
            "total_committees": len(committees),
            "by_type": {},
            "by_chamber": {},
            "isvp_compatible": 0,
            "with_subcommittees": 0
        }
        
        for committee in committees.values():
            # Count by type
            summary["by_type"][committee.type] = summary["by_type"].get(committee.type, 0) + 1
            
            # Count by chamber
            summary["by_chamber"][committee.chamber] = summary["by_chamber"].get(committee.chamber, 0) + 1
            
            # Count ISVP compatible
            if committee.isvp_compatible:
                summary["isvp_compatible"] += 1
            
            # Count with subcommittees
            if committee.subcommittees:
                summary["with_subcommittees"] += 1
        
        return summary

def main():
    """Main discovery function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Discover Senate Committee Structure")
    parser.add_argument("--output", default="data/committees", help="Output directory")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize discovery system
    discovery = CommitteeDiscovery(args.output)
    
    # Discover all committees
    committees = discovery.discover_all_committees()
    
    # Save results
    output_file = discovery.save_committee_structure()
    
    # Generate summary
    summary = discovery.generate_committee_summary()
    
    print("\n" + "="*60)
    print("COMMITTEE DISCOVERY COMPLETE")
    print("="*60)
    print(f"Total Committees: {summary['total_committees']}")
    print(f"ISVP Compatible: {summary['isvp_compatible']}")
    print(f"With Subcommittees: {summary['with_subcommittees']}")
    print("\nBy Type:")
    for type_name, count in summary['by_type'].items():
        print(f"  {type_name.title()}: {count}")
    print("\nBy Chamber:")
    for chamber, count in summary['by_chamber'].items():
        print(f"  {chamber}: {count}")
    print(f"\nResults saved to: {output_file}")
    print("="*60)

if __name__ == "__main__":
    main()