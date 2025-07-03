#!/usr/bin/env python3
"""
Committee Structure Validation System
Validates discovered committees against official Senate sources
"""

import json
import requests
from pathlib import Path
from typing import Dict, List, Set, Tuple
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import re

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommitteeValidator:
    """Validates committee discovery results"""
    
    def __init__(self, committee_file: str = "data/committees/committee_structure.json"):
        self.committee_file = Path(committee_file)
        self.committees = self._load_committees()
        
        # Official Senate sources for validation
        self.validation_sources = {
            "senate_committees": "https://www.senate.gov/committees/",
            "senate_leadership": "https://www.senate.gov/senators/leadership.htm",
            "congress_gov": "https://www.congress.gov/committees"
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Senate Committee Validation System (Research/Academic)'
        })
        
        # Known committee mappings for validation
        self.known_valid_committees = {
            "SCOM": "Commerce, Science, and Transportation",
            "SSCI": "Intelligence",
            "SBAN": "Banking, Housing, and Urban Affairs", 
            "SSJU": "Judiciary",
            "SFRC": "Foreign Relations",
            "SASC": "Armed Services",
            "SSVA": "Veterans' Affairs",
            "SENV": "Environment and Public Works",
            "HELP": "Health, Education, Labor and Pensions",
            "SAGR": "Agriculture, Nutrition, and Forestry",
            "SENE": "Energy and Natural Resources",
            "SHSG": "Homeland Security and Governmental Affairs",
            "SAPP": "Appropriations",
            "SBUD": "Budget",
            "SRUL": "Rules and Administration",
            "SMAL": "Small Business and Entrepreneurship",
            "SFIN": "Finance",
            "SINT": "Indian Affairs"
        }
    
    def _load_committees(self) -> Dict:
        """Load discovered committees"""
        if not self.committee_file.exists():
            logger.error(f"Committee file not found: {self.committee_file}")
            return {}
        
        try:
            with open(self.committee_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load committees: {e}")
            return {}
    
    def validate_against_official_sources(self) -> Dict:
        """Validate against official Senate sources"""
        logger.info("Validating committees against official sources...")
        
        validation_results = {
            "total_committees": len(self.committees.get("committees", {})),
            "validated_committees": 0,
            "missing_committees": [],
            "unknown_committees": [],
            "validation_errors": [],
            "validation_date": datetime.now().isoformat()
        }
        
        # Validate against known committees
        discovered_codes = set(self.committees.get("committees", {}).keys())
        known_codes = set(self.known_valid_committees.keys())
        
        # Check for missing known committees
        missing = known_codes - discovered_codes
        validation_results["missing_committees"] = list(missing)
        
        # Check for unknown committees
        unknown = discovered_codes - known_codes
        validation_results["unknown_committees"] = list(unknown)
        
        # Validate discovered committees
        for code, committee in self.committees.get("committees", {}).items():
            if code in self.known_valid_committees:
                expected_name = self.known_valid_committees[code]
                actual_name = committee.get("name", "")
                
                if expected_name.lower() in actual_name.lower() or \
                   actual_name.lower() in expected_name.lower():
                    validation_results["validated_committees"] += 1
                else:
                    validation_results["validation_errors"].append({
                        "code": code,
                        "expected": expected_name,
                        "actual": actual_name,
                        "error": "Name mismatch"
                    })
        
        # Validate against live Senate website
        try:
            live_validation = self._validate_against_senate_website()
            validation_results["live_validation"] = live_validation
        except Exception as e:
            validation_results["live_validation_error"] = str(e)
        
        logger.info(f"Validation complete: {validation_results['validated_committees']} committees validated")
        return validation_results
    
    def _validate_against_senate_website(self) -> Dict:
        """Validate against live Senate website"""
        logger.info("Validating against Senate.gov...")
        
        try:
            response = self.session.get(self.validation_sources["senate_committees"])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract committee names from website
            website_committees = set()
            
            # Look for committee links
            committee_links = soup.find_all('a', href=True)
            for link in committee_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                if ('committee' in href.lower() or 'committees' in href.lower()) and \
                   len(text) > 5 and 'Committee' in text:
                    # Clean up committee name
                    clean_name = re.sub(r'(Committee on |Senate )', '', text)
                    website_committees.add(clean_name.strip())
            
            # Compare with discovered committees
            discovered_names = set()
            for committee in self.committees.get("committees", {}).values():
                discovered_names.add(committee.get("name", ""))
            
            matches = 0
            for discovered in discovered_names:
                for website in website_committees:
                    if discovered.lower() in website.lower() or \
                       website.lower() in discovered.lower():
                        matches += 1
                        break
            
            return {
                "website_committees_found": len(website_committees),
                "discovered_committees": len(discovered_names),
                "matches": matches,
                "match_rate": matches / len(discovered_names) if discovered_names else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to validate against Senate website: {e}")
            return {"error": str(e)}
    
    def check_isvp_compatibility(self) -> Dict:
        """Check ISVP compatibility claims"""
        logger.info("Checking ISVP compatibility...")
        
        compatibility_results = {
            "total_committees": 0,
            "claimed_isvp_compatible": 0,
            "validated_isvp_compatible": 0,
            "isvp_validation_results": []
        }
        
        for code, committee in self.committees.get("committees", {}).items():
            compatibility_results["total_committees"] += 1
            
            if committee.get("isvp_compatible"):
                compatibility_results["claimed_isvp_compatible"] += 1
                
                # Validate ISVP compatibility
                validation_result = self._validate_isvp_compatibility(committee)
                compatibility_results["isvp_validation_results"].append(validation_result)
                
                if validation_result["is_compatible"]:
                    compatibility_results["validated_isvp_compatible"] += 1
        
        return compatibility_results
    
    def _validate_isvp_compatibility(self, committee: Dict) -> Dict:
        """Validate ISVP compatibility for a committee"""
        result = {
            "code": committee.get("code"),
            "name": committee.get("name"),
            "website_url": committee.get("website_url"),
            "is_compatible": False,
            "validation_method": "website_check",
            "details": {}
        }
        
        if not committee.get("website_url"):
            result["details"]["error"] = "No website URL provided"
            return result
        
        try:
            response = self.session.get(committee["website_url"], timeout=10)
            response.raise_for_status()
            
            content = response.text.lower()
            
            # Check for ISVP indicators
            isvp_indicators = [
                "isvp",
                "in-house streaming",
                "senate.gov/isvp",
                "streaming video player",
                "live.senate.gov"
            ]
            
            found_indicators = []
            for indicator in isvp_indicators:
                if indicator in content:
                    found_indicators.append(indicator)
            
            result["is_compatible"] = len(found_indicators) > 0
            result["details"]["found_indicators"] = found_indicators
            result["details"]["response_status"] = response.status_code
            
        except Exception as e:
            result["details"]["error"] = str(e)
        
        return result
    
    def validate_subcommittee_structure(self) -> Dict:
        """Validate subcommittee structure"""
        logger.info("Validating subcommittee structure...")
        
        subcommittee_results = {
            "committees_with_subcommittees": 0,
            "total_subcommittees": 0,
            "orphaned_subcommittees": [],
            "structural_errors": []
        }
        
        parent_committees = set()
        subcommittees = []
        
        for code, committee in self.committees.get("committees", {}).items():
            if committee.get("type") == "committee":
                parent_committees.add(code)
                if committee.get("subcommittees"):
                    subcommittee_results["committees_with_subcommittees"] += 1
            elif committee.get("type") == "subcommittee":
                subcommittees.append(committee)
                subcommittee_results["total_subcommittees"] += 1
        
        # Check for orphaned subcommittees
        for subcommittee in subcommittees:
            parent_code = subcommittee.get("parent_code")
            if parent_code and parent_code not in parent_committees:
                subcommittee_results["orphaned_subcommittees"].append({
                    "code": subcommittee.get("code"),
                    "name": subcommittee.get("name"),
                    "parent_code": parent_code
                })
        
        # Check for structural consistency
        for code, committee in self.committees.get("committees", {}).items():
            if committee.get("subcommittees"):
                for sub_code in committee["subcommittees"]:
                    if sub_code not in self.committees.get("committees", {}):
                        subcommittee_results["structural_errors"].append({
                            "parent_code": code,
                            "missing_subcommittee": sub_code
                        })
        
        return subcommittee_results
    
    def generate_validation_report(self) -> Dict:
        """Generate comprehensive validation report"""
        logger.info("Generating validation report...")
        
        report = {
            "validation_date": datetime.now().isoformat(),
            "committee_file": str(self.committee_file),
            "official_validation": self.validate_against_official_sources(),
            "isvp_compatibility": self.check_isvp_compatibility(),
            "subcommittee_structure": self.validate_subcommittee_structure()
        }
        
        # Calculate overall validation score
        official = report["official_validation"]
        total_committees = official["total_committees"]
        validated = official["validated_committees"]
        
        if total_committees > 0:
            validation_score = (validated / total_committees) * 100
            report["overall_validation_score"] = validation_score
            
            if validation_score >= 80:
                report["validation_status"] = "EXCELLENT"
            elif validation_score >= 60:
                report["validation_status"] = "GOOD"
            elif validation_score >= 40:
                report["validation_status"] = "FAIR"
            else:
                report["validation_status"] = "NEEDS_IMPROVEMENT"
        else:
            report["validation_status"] = "NO_DATA"
        
        return report
    
    def save_validation_report(self, report: Dict, output_file: str = "committee_validation_report.json"):
        """Save validation report"""
        output_path = self.committee_file.parent / output_file
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Validation report saved to {output_path}")
        return output_path

def main():
    """Main validation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate Committee Structure")
    parser.add_argument("--committee-file", default="data/committees/committee_structure.json", 
                       help="Committee structure file")
    parser.add_argument("--compare-official", action="store_true", 
                       help="Compare with official sources")
    parser.add_argument("--output", default="committee_validation_report.json", 
                       help="Output report file")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize validator
    validator = CommitteeValidator(args.committee_file)
    
    # Generate validation report
    report = validator.generate_validation_report()
    
    # Save report
    output_file = validator.save_validation_report(report, args.output)
    
    # Print summary
    print("\n" + "="*60)
    print("COMMITTEE VALIDATION COMPLETE")
    print("="*60)
    print(f"Validation Status: {report['validation_status']}")
    print(f"Overall Score: {report.get('overall_validation_score', 0):.1f}%")
    print(f"Validated Committees: {report['official_validation']['validated_committees']}")
    print(f"Total Committees: {report['official_validation']['total_committees']}")
    print(f"ISVP Compatible: {report['isvp_compatibility']['validated_isvp_compatible']}")
    print(f"Subcommittees: {report['subcommittee_structure']['total_subcommittees']}")
    
    if report['official_validation']['missing_committees']:
        print(f"\nMissing Committees: {len(report['official_validation']['missing_committees'])}")
        for missing in report['official_validation']['missing_committees'][:5]:
            print(f"  - {missing}")
    
    if report['official_validation']['unknown_committees']:
        print(f"\nUnknown Committees: {len(report['official_validation']['unknown_committees'])}")
        for unknown in report['official_validation']['unknown_committees'][:5]:
            print(f"  - {unknown}")
    
    print(f"\nValidation report saved to: {output_file}")
    print("="*60)

if __name__ == "__main__":
    main()