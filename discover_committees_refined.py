#!/usr/bin/env python3
"""
Refined Committee Discovery System
Focuses on actual Senate committees with better filtering
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

class RefinedCommitteeDiscovery:
    """Refined Senate Committee Discovery System"""
    
    def __init__(self, output_dir: str = "data/committees"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Definitive list of Senate committees (119th Congress)
        self.senate_committees = {
            "SASC": {
                "name": "Armed Services",
                "full_name": "Committee on Armed Services",
                "website": "https://www.armed-services.senate.gov/",
                "jurisdiction": "Military affairs, defense policy"
            },
            "SAPP": {
                "name": "Appropriations", 
                "full_name": "Committee on Appropriations",
                "website": "https://www.appropriations.senate.gov/",
                "jurisdiction": "Federal spending, budget allocation"
            },
            "SBAN": {
                "name": "Banking, Housing, and Urban Affairs",
                "full_name": "Committee on Banking, Housing, and Urban Affairs", 
                "website": "https://www.banking.senate.gov/",
                "jurisdiction": "Banking, housing, urban development",
                "isvp_compatible": True
            },
            "SBUD": {
                "name": "Budget",
                "full_name": "Committee on the Budget",
                "website": "https://www.budget.senate.gov/",
                "jurisdiction": "Federal budget process"
            },
            "SCOM": {
                "name": "Commerce, Science, and Transportation",
                "full_name": "Committee on Commerce, Science, and Transportation",
                "website": "https://www.commerce.senate.gov/",
                "jurisdiction": "Interstate commerce, transportation, telecommunications",
                "isvp_compatible": True
            },
            "SENV": {
                "name": "Environment and Public Works",
                "full_name": "Committee on Environment and Public Works",
                "website": "https://www.epw.senate.gov/",
                "jurisdiction": "Environmental protection, public works"
            },
            "SENE": {
                "name": "Energy and Natural Resources",
                "full_name": "Committee on Energy and Natural Resources",
                "website": "https://www.energy.senate.gov/",
                "jurisdiction": "Energy policy, natural resources"
            },
            "SFIN": {
                "name": "Finance",
                "full_name": "Committee on Finance",
                "website": "https://www.finance.senate.gov/",
                "jurisdiction": "Taxation, trade, Social Security"
            },
            "SFRC": {
                "name": "Foreign Relations",
                "full_name": "Committee on Foreign Relations",
                "website": "https://www.foreign.senate.gov/",
                "jurisdiction": "Foreign policy, treaties"
            },
            "HELP": {
                "name": "Health, Education, Labor and Pensions",
                "full_name": "Committee on Health, Education, Labor and Pensions",
                "website": "https://www.help.senate.gov/",
                "jurisdiction": "Health care, education, labor"
            },
            "SHSG": {
                "name": "Homeland Security and Governmental Affairs",
                "full_name": "Committee on Homeland Security and Governmental Affairs",
                "website": "https://www.hsgac.senate.gov/",
                "jurisdiction": "Homeland security, government operations"
            },
            "SINT": {
                "name": "Indian Affairs",
                "full_name": "Committee on Indian Affairs",
                "website": "https://www.indian.senate.gov/",
                "jurisdiction": "Native American affairs"
            },
            "SSCI": {
                "name": "Intelligence",
                "full_name": "Select Committee on Intelligence",
                "website": "https://www.intelligence.senate.gov/",
                "jurisdiction": "Intelligence activities and programs",
                "isvp_compatible": True,
                "type": "select"
            },
            "SSJU": {
                "name": "Judiciary",
                "full_name": "Committee on the Judiciary",
                "website": "https://www.judiciary.senate.gov/",
                "jurisdiction": "Federal courts, constitutional law",
                "isvp_compatible": True
            },
            "SRUL": {
                "name": "Rules and Administration",
                "full_name": "Committee on Rules and Administration",
                "website": "https://www.rules.senate.gov/",
                "jurisdiction": "Senate rules, federal elections"
            },
            "SMAL": {
                "name": "Small Business and Entrepreneurship",
                "full_name": "Committee on Small Business and Entrepreneurship",
                "website": "https://www.sbc.senate.gov/",
                "jurisdiction": "Small business policy"
            },
            "SSVA": {
                "name": "Veterans' Affairs",
                "full_name": "Committee on Veterans' Affairs",
                "website": "https://www.veterans.senate.gov/",
                "jurisdiction": "Veterans programs and benefits"
            },
            "SAGR": {
                "name": "Agriculture, Nutrition, and Forestry",
                "full_name": "Committee on Agriculture, Nutrition, and Forestry",
                "website": "https://www.agriculture.senate.gov/",
                "jurisdiction": "Agriculture, nutrition, forestry"
            }
        }
        
        # Select committees
        self.select_committees = {
            "SSAG": {
                "name": "Aging",
                "full_name": "Special Committee on Aging",
                "website": "https://www.aging.senate.gov/",
                "jurisdiction": "Issues affecting older Americans",
                "type": "select"
            },
            "SSET": {
                "name": "Ethics",
                "full_name": "Select Committee on Ethics",
                "website": "https://www.ethics.senate.gov/",
                "jurisdiction": "Senate ethics, conduct",
                "type": "select"
            }
        }
        
        self.discovered_committees: Dict[str, Committee] = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Senate Hearing Audio Capture System (Research/Academic)'
        })
        
    def create_committee_structure(self) -> Dict[str, Committee]:
        """Create committee structure from definitive list"""
        logger.info("Creating committee structure from definitive list...")
        
        committees = {}
        
        # Add standing committees
        for code, details in self.senate_committees.items():
            committee = Committee(
                code=code,
                name=details["name"],
                full_name=details["full_name"],
                chamber="Senate",
                type=details.get("type", "committee"),
                website_url=details.get("website"),
                isvp_compatible=details.get("isvp_compatible", False),
                jurisdiction=details.get("jurisdiction"),
                api_source="Definitive Senate committee list",
                discovery_date=datetime.now().isoformat()
            )
            committees[code] = committee
        
        # Add select committees
        for code, details in self.select_committees.items():
            committee = Committee(
                code=code,
                name=details["name"],
                full_name=details["full_name"],
                chamber="Senate",
                type=details.get("type", "select"),
                website_url=details.get("website"),
                isvp_compatible=details.get("isvp_compatible", False),
                jurisdiction=details.get("jurisdiction"),
                api_source="Definitive Senate committee list",
                discovery_date=datetime.now().isoformat()
            )
            committees[code] = committee
        
        logger.info(f"Created {len(committees)} committees from definitive list")
        return committees
    
    def discover_subcommittees(self, committee: Committee) -> List[Committee]:
        """Discover subcommittees for a specific committee"""
        logger.info(f"Discovering subcommittees for {committee.name}")
        
        subcommittees = []
        
        if not committee.website_url:
            logger.debug(f"No website URL for {committee.name}")
            return subcommittees
        
        try:
            response = self.session.get(committee.website_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for subcommittee patterns
            subcommittee_patterns = [
                r'subcommittee\s+on\s+([^<>\n]+)',
                r'subcommittee\s+for\s+([^<>\n]+)',
                r'(?:sub|sub-committee)\s*[:]\s*([^<>\n]+)'
            ]
            
            found_subcommittees = set()
            
            # Search in text content
            page_text = soup.get_text()
            for pattern in subcommittee_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    clean_match = re.sub(r'[^\w\s,&-]', '', match).strip()
                    if len(clean_match) > 5 and len(clean_match) < 100:
                        found_subcommittees.add(clean_match)
            
            # Search in link text
            links = soup.find_all('a', href=True)
            for link in links:
                text = link.get_text(strip=True)
                if 'subcommittee' in text.lower() and len(text) > 5:
                    clean_text = re.sub(r'[^\w\s,&-]', '', text).strip()
                    if len(clean_text) > 5 and len(clean_text) < 100:
                        found_subcommittees.add(clean_text)
            
            # Create subcommittee objects
            for sub_name in found_subcommittees:
                sub_code = f"{committee.code}_{self._generate_subcommittee_code(sub_name)}"
                
                subcommittee = Committee(
                    code=sub_code,
                    name=sub_name,
                    full_name=f"Subcommittee on {sub_name}",
                    chamber="Senate",
                    type="subcommittee",
                    parent_code=committee.code,
                    website_url=committee.website_url,  # Use parent URL for now
                    api_source=f"Discovered from {committee.name} website",
                    discovery_date=datetime.now().isoformat()
                )
                
                subcommittees.append(subcommittee)
            
            logger.info(f"Found {len(subcommittees)} subcommittees for {committee.name}")
            
        except Exception as e:
            logger.warning(f"Failed to discover subcommittees for {committee.name}: {e}")
        
        return subcommittees
    
    def _generate_subcommittee_code(self, name: str) -> str:
        """Generate subcommittee code from name"""
        # Remove common words and clean
        name = re.sub(r'\b(subcommittee|on|the|and|&|of|for|in|to|a|an)\b', '', name, flags=re.I)
        
        # Get meaningful words
        words = [word.strip() for word in name.split() if len(word.strip()) > 2]
        
        # Create code
        if len(words) >= 2:
            return words[0][:3].upper() + words[1][:3].upper()
        elif len(words) == 1:
            return words[0][:6].upper()
        else:
            return "SUB"
    
    def enhance_committee_data(self, committees: Dict[str, Committee]) -> Dict[str, Committee]:
        """Enhance committee data with additional information"""
        logger.info("Enhancing committee data...")
        
        enhanced_committees = {}
        
        for code, committee in committees.items():
            enhanced_committee = committee
            
            # Discover subcommittees
            if committee.type == "committee":
                subcommittees = self.discover_subcommittees(committee)
                if subcommittees:
                    enhanced_committee.subcommittees = [sub.code for sub in subcommittees]
                    
                    # Add subcommittees to the collection
                    for sub in subcommittees:
                        enhanced_committees[sub.code] = sub
            
            # Validate ISVP compatibility
            if committee.isvp_compatible and committee.website_url:
                try:
                    response = self.session.get(committee.website_url, timeout=10)
                    if response.status_code == 200:
                        content = response.text.lower()
                        isvp_indicators = ["isvp", "streaming", "video", "live"]
                        if any(indicator in content for indicator in isvp_indicators):
                            enhanced_committee.isvp_compatible = True
                        else:
                            enhanced_committee.isvp_compatible = False
                except:
                    pass
            
            enhanced_committees[code] = enhanced_committee
        
        logger.info(f"Enhanced {len(committees)} committees, total with subcommittees: {len(enhanced_committees)}")
        return enhanced_committees
    
    def discover_all_committees(self) -> Dict[str, Committee]:
        """Discover all committees using refined approach"""
        logger.info("Starting refined committee discovery...")
        
        # Create base committee structure
        committees = self.create_committee_structure()
        
        # Enhance with additional data
        enhanced_committees = self.enhance_committee_data(committees)
        
        self.discovered_committees = enhanced_committees
        logger.info(f"Total committees discovered: {len(enhanced_committees)}")
        
        return enhanced_committees
    
    def save_committee_structure(self, output_file: str = "committee_structure_refined.json"):
        """Save refined committee structure"""
        output_path = self.output_dir / output_file
        
        # Convert to serializable format
        committee_data = {
            "discovery_info": {
                "discovery_date": datetime.now().isoformat(),
                "discovery_method": "Refined definitive list",
                "total_committees": len(self.discovered_committees),
                "sources": ["Definitive Senate committee list", "Committee website subcommittee discovery"],
                "isvp_compatible_count": len([c for c in self.discovered_committees.values() 
                                            if c.isvp_compatible]),
                "standing_committees": len([c for c in self.discovered_committees.values() 
                                          if c.type == "committee"]),
                "select_committees": len([c for c in self.discovered_committees.values() 
                                        if c.type == "select"]),
                "subcommittees": len([c for c in self.discovered_committees.values() 
                                    if c.type == "subcommittee"])
            },
            "committees": {code: asdict(committee) for code, committee in self.discovered_committees.items()}
        }
        
        with open(output_path, 'w') as f:
            json.dump(committee_data, f, indent=2)
        
        logger.info(f"Refined committee structure saved to {output_path}")
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
    """Main refined discovery function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Refined Senate Committee Discovery")
    parser.add_argument("--output", default="data/committees", help="Output directory")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize refined discovery system
    discovery = RefinedCommitteeDiscovery(args.output)
    
    # Discover all committees
    committees = discovery.discover_all_committees()
    
    # Save results
    output_file = discovery.save_committee_structure()
    
    # Generate summary
    summary = discovery.generate_committee_summary()
    
    print("\n" + "="*60)
    print("REFINED COMMITTEE DISCOVERY COMPLETE")
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