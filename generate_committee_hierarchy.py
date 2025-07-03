#!/usr/bin/env python3
"""
Committee Hierarchy Generator
Creates organized committee hierarchy for navigation and management
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommitteeHierarchyGenerator:
    """Generates organized committee hierarchy"""
    
    def __init__(self, committee_file: str = "data/committees/committee_structure.json"):
        self.committee_file = Path(committee_file)
        self.committees = self._load_committees()
        
    def _load_committees(self) -> Dict:
        """Load committee structure"""
        if not self.committee_file.exists():
            logger.error(f"Committee file not found: {self.committee_file}")
            return {}
        
        try:
            with open(self.committee_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load committees: {e}")
            return {}
    
    def generate_hierarchy(self) -> Dict:
        """Generate organized committee hierarchy"""
        logger.info("Generating committee hierarchy...")
        
        hierarchy = {
            "generation_date": datetime.now().isoformat(),
            "source_file": str(self.committee_file),
            "structure": {
                "standing_committees": [],
                "select_committees": [],
                "joint_committees": [],
                "special_committees": []
            },
            "statistics": {
                "total_committees": 0,
                "total_subcommittees": 0,
                "isvp_compatible": 0,
                "with_subcommittees": 0
            }
        }
        
        committees = self.committees.get("committees", {})
        
        for code, committee in committees.items():
            committee_type = committee.get("type", "committee")
            chamber = committee.get("chamber", "Senate")
            
            # Skip subcommittees for now (they'll be nested under parents)
            if committee_type == "subcommittee":
                hierarchy["statistics"]["total_subcommittees"] += 1
                continue
            
            # Create committee entry
            committee_entry = self._create_committee_entry(code, committee, committees)
            
            # Categorize committee
            if committee_type == "committee" and chamber == "Senate":
                hierarchy["structure"]["standing_committees"].append(committee_entry)
            elif committee_type == "select" and chamber == "Senate":
                hierarchy["structure"]["select_committees"].append(committee_entry)
            elif committee_type == "joint":
                hierarchy["structure"]["joint_committees"].append(committee_entry)
            else:
                hierarchy["structure"]["special_committees"].append(committee_entry)
            
            # Update statistics
            hierarchy["statistics"]["total_committees"] += 1
            
            if committee.get("isvp_compatible"):
                hierarchy["statistics"]["isvp_compatible"] += 1
            
            if committee.get("subcommittees"):
                hierarchy["statistics"]["with_subcommittees"] += 1
        
        # Sort committees by name within each category
        for category in hierarchy["structure"].values():
            if isinstance(category, list):
                category.sort(key=lambda x: x.get("name", ""))
        
        logger.info(f"Generated hierarchy with {hierarchy['statistics']['total_committees']} committees")
        return hierarchy
    
    def _create_committee_entry(self, code: str, committee: Dict, all_committees: Dict) -> Dict:
        """Create detailed committee entry"""
        entry = {
            "code": code,
            "name": committee.get("name", ""),
            "full_name": committee.get("full_name", ""),
            "type": committee.get("type", "committee"),
            "chamber": committee.get("chamber", "Senate"),
            "website_url": committee.get("website_url"),
            "jurisdiction": committee.get("jurisdiction"),
            "isvp_compatible": committee.get("isvp_compatible", False),
            "member_count": committee.get("member_count"),
            "chair": committee.get("chair"),
            "ranking_member": committee.get("ranking_member"),
            "subcommittees": [],
            "metadata": {
                "discovery_date": committee.get("discovery_date"),
                "api_source": committee.get("api_source")
            }
        }
        
        # Add subcommittees if any
        if committee.get("subcommittees"):
            for sub_code in committee["subcommittees"]:
                if sub_code in all_committees:
                    sub_committee = all_committees[sub_code]
                    sub_entry = {
                        "code": sub_code,
                        "name": sub_committee.get("name", ""),
                        "full_name": sub_committee.get("full_name", ""),
                        "website_url": sub_committee.get("website_url"),
                        "parent_code": code,
                        "isvp_compatible": sub_committee.get("isvp_compatible", False),
                        "metadata": {
                            "discovery_date": sub_committee.get("discovery_date"),
                            "api_source": sub_committee.get("api_source")
                        }
                    }
                    entry["subcommittees"].append(sub_entry)
            
            # Sort subcommittees by name
            entry["subcommittees"].sort(key=lambda x: x.get("name", ""))
        
        return entry
    
    def generate_navigation_structure(self) -> Dict:
        """Generate navigation-friendly structure"""
        logger.info("Generating navigation structure...")
        
        hierarchy = self.generate_hierarchy()
        
        navigation = {
            "generation_date": datetime.now().isoformat(),
            "categories": [],
            "quick_access": {
                "isvp_compatible": [],
                "most_active": [],
                "priority_committees": []
            },
            "search_index": []
        }
        
        # Process each category
        for category_name, committees in hierarchy["structure"].items():
            if not committees:
                continue
                
            category = {
                "name": category_name.replace("_", " ").title(),
                "code": category_name,
                "count": len(committees),
                "committees": []
            }
            
            for committee in committees:
                nav_committee = {
                    "code": committee["code"],
                    "name": committee["name"],
                    "isvp_compatible": committee["isvp_compatible"],
                    "subcommittee_count": len(committee.get("subcommittees", [])),
                    "website_url": committee.get("website_url"),
                    "has_subcommittees": len(committee.get("subcommittees", [])) > 0
                }
                
                category["committees"].append(nav_committee)
                
                # Add to quick access if ISVP compatible
                if committee["isvp_compatible"]:
                    navigation["quick_access"]["isvp_compatible"].append(nav_committee)
                
                # Add to search index
                search_entry = {
                    "code": committee["code"],
                    "name": committee["name"],
                    "full_name": committee["full_name"],
                    "keywords": self._generate_search_keywords(committee),
                    "category": category_name,
                    "isvp_compatible": committee["isvp_compatible"]
                }
                navigation["search_index"].append(search_entry)
            
            navigation["categories"].append(category)
        
        # Generate priority committees (ISVP compatible + high activity)
        priority_codes = ["SCOM", "SSCI", "SBAN", "SSJU", "SFRC", "SASC", "HELP"]
        for committee in navigation["search_index"]:
            if committee["code"] in priority_codes:
                navigation["quick_access"]["priority_committees"].append({
                    "code": committee["code"],
                    "name": committee["name"],
                    "isvp_compatible": committee["isvp_compatible"]
                })
        
        logger.info(f"Generated navigation structure with {len(navigation['categories'])} categories")
        return navigation
    
    def _generate_search_keywords(self, committee: Dict) -> List[str]:
        """Generate search keywords for committee"""
        keywords = []
        
        # Add name words
        name_words = committee.get("name", "").split()
        keywords.extend([word.lower() for word in name_words if len(word) > 2])
        
        # Add full name words
        full_name_words = committee.get("full_name", "").split()
        keywords.extend([word.lower() for word in full_name_words if len(word) > 2])
        
        # Add jurisdiction words
        if committee.get("jurisdiction"):
            jurisdiction_words = committee["jurisdiction"].split()
            keywords.extend([word.lower() for word in jurisdiction_words if len(word) > 2])
        
        # Remove duplicates and common words
        common_words = {"committee", "senate", "house", "the", "and", "of", "on", "for", "to", "in"}
        keywords = list(set(keywords) - common_words)
        
        return keywords
    
    def save_hierarchy(self, hierarchy: Dict, output_file: str = "committee_hierarchy.json"):
        """Save committee hierarchy"""
        output_path = self.committee_file.parent / output_file
        
        with open(output_path, 'w') as f:
            json.dump(hierarchy, f, indent=2)
        
        logger.info(f"Hierarchy saved to {output_path}")
        return output_path
    
    def save_navigation_structure(self, navigation: Dict, output_file: str = "committee_navigation.json"):
        """Save navigation structure"""
        output_path = self.committee_file.parent / output_file
        
        with open(output_path, 'w') as f:
            json.dump(navigation, f, indent=2)
        
        logger.info(f"Navigation structure saved to {output_path}")
        return output_path

def main():
    """Main hierarchy generation function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Committee Hierarchy")
    parser.add_argument("--committee-file", default="data/committees/committee_structure.json",
                       help="Committee structure file")
    parser.add_argument("--output", default="data/committee_hierarchy.json",
                       help="Output hierarchy file")
    parser.add_argument("--navigation", action="store_true",
                       help="Generate navigation structure")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize generator
    generator = CommitteeHierarchyGenerator(args.committee_file)
    
    # Generate hierarchy
    hierarchy = generator.generate_hierarchy()
    
    # Save hierarchy
    hierarchy_file = generator.save_hierarchy(hierarchy, "committee_hierarchy.json")
    
    # Generate navigation structure if requested
    if args.navigation:
        navigation = generator.generate_navigation_structure()
        navigation_file = generator.save_navigation_structure(navigation, "committee_navigation.json")
    
    # Print summary
    print("\n" + "="*60)
    print("COMMITTEE HIERARCHY GENERATION COMPLETE")
    print("="*60)
    print(f"Total Committees: {hierarchy['statistics']['total_committees']}")
    print(f"Total Subcommittees: {hierarchy['statistics']['total_subcommittees']}")
    print(f"ISVP Compatible: {hierarchy['statistics']['isvp_compatible']}")
    print(f"With Subcommittees: {hierarchy['statistics']['with_subcommittees']}")
    print("\nBy Category:")
    for category, committees in hierarchy['structure'].items():
        if committees:
            print(f"  {category.replace('_', ' ').title()}: {len(committees)}")
    
    print(f"\nHierarchy saved to: {hierarchy_file}")
    if args.navigation:
        print(f"Navigation structure saved to: {navigation_file}")
    print("="*60)

if __name__ == "__main__":
    main()