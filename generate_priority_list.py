#!/usr/bin/env python3
"""
Priority Hearing Selection System
Generates curated test list for systematic validation
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
import statistics

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PriorityHearingSelector:
    """Generates priority hearing lists for testing"""
    
    def __init__(self, 
                 catalog_file: str = "data/hearings/hearing_catalog.json",
                 readiness_file: str = "data/hearings/hearing_readiness_report.json"):
        self.catalog_file = Path(catalog_file)
        self.readiness_file = Path(readiness_file)
        
        self.hearings = self._load_hearings()
        self.readiness_data = self._load_readiness_data()
        
        # Priority criteria
        self.priority_criteria = {
            "isvp_compatibility": 5,
            "committee_diversity": 3,
            "duration_variety": 2,
            "recency": 2,
            "complexity_range": 2,
            "audio_quality": 4
        }
        
        # Target committee distribution for testing
        self.target_committees = {
            "SCOM": {"name": "Commerce, Science, and Transportation", "priority": 10},
            "SSCI": {"name": "Intelligence", "priority": 10},
            "SBAN": {"name": "Banking, Housing, and Urban Affairs", "priority": 10},
            "SSJU": {"name": "Judiciary", "priority": 10},
            "SFRC": {"name": "Foreign Relations", "priority": 8},
            "SASC": {"name": "Armed Services", "priority": 8},
            "HELP": {"name": "Health, Education, Labor and Pensions", "priority": 7},
            "SAPP": {"name": "Appropriations", "priority": 6},
            "SENV": {"name": "Environment and Public Works", "priority": 6},
            "SENE": {"name": "Energy and Natural Resources", "priority": 5}
        }
        
    def _load_hearings(self) -> Dict:
        """Load hearing catalog"""
        if not self.catalog_file.exists():
            logger.error(f"Catalog file not found: {self.catalog_file}")
            return {}
        
        try:
            with open(self.catalog_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load catalog: {e}")
            return {}
    
    def _load_readiness_data(self) -> Dict:
        """Load readiness assessment data"""
        if not self.readiness_file.exists():
            logger.warning(f"Readiness file not found: {self.readiness_file}")
            return {}
        
        try:
            with open(self.readiness_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load readiness data: {e}")
            return {}
    
    def select_priority_hearings(self, target_count: int = 20) -> List[Dict]:
        """Select priority hearings for testing"""
        logger.info(f"Selecting {target_count} priority hearings...")
        
        hearings = self.hearings.get("hearings", {})
        readiness_recommendations = self.readiness_data.get("recommendations", {})
        
        # Get immediate processing candidates
        immediate_candidates = readiness_recommendations.get("immediate_processing", [])
        good_candidates = readiness_recommendations.get("requires_preparation", [])
        
        # Combine candidates
        all_candidates = immediate_candidates + good_candidates
        
        # Score and rank candidates
        scored_candidates = []
        for candidate in all_candidates:
            hearing_id = candidate["hearing_id"]
            hearing_data = hearings.get(hearing_id, {})
            
            if hearing_data:
                priority_score = self._calculate_priority_score(hearing_data, candidate)
                
                scored_candidate = {
                    "hearing_id": hearing_id,
                    "title": candidate["title"],
                    "committee_code": candidate["committee"],
                    "committee_name": self.target_committees.get(candidate["committee"], {}).get("name", candidate["committee"]),
                    "readiness_score": candidate["score"],
                    "priority_score": priority_score,
                    "audio_source": candidate.get("audio_source", "Unknown"),
                    "isvp_compatible": hearing_data.get("isvp_compatible", False),
                    "date": hearing_data.get("date"),
                    "witnesses": hearing_data.get("witnesses", []),
                    "witness_count": len(hearing_data.get("witnesses", [])),
                    "url": hearing_data.get("url"),
                    "rationale": self._generate_selection_rationale(hearing_data, candidate)
                }
                
                scored_candidates.append(scored_candidate)
        
        # Sort by priority score
        scored_candidates.sort(key=lambda x: x["priority_score"], reverse=True)
        
        # Apply diversity filters
        diverse_candidates = self._apply_diversity_filters(scored_candidates, target_count)
        
        logger.info(f"Selected {len(diverse_candidates)} priority hearings")
        return diverse_candidates
    
    def _calculate_priority_score(self, hearing_data: Dict, candidate: Dict) -> float:
        """Calculate priority score for hearing"""
        score = 0.0
        
        # Base readiness score
        score += candidate.get("score", 0) * 30
        
        # Committee priority
        committee_code = candidate.get("committee", "")
        committee_priority = self.target_committees.get(committee_code, {}).get("priority", 1)
        score += committee_priority * 3
        
        # ISVP compatibility bonus
        if hearing_data.get("isvp_compatible"):
            score += 20
        
        # Audio source quality
        audio_source = candidate.get("audio_source", "None")
        if audio_source == "ISVP":
            score += 15
        elif audio_source == "YouTube":
            score += 10
        
        # Recency bonus
        date_str = hearing_data.get("date", "")
        if date_str and "2025" in date_str:
            score += 10
        
        # Witness availability
        witness_count = len(hearing_data.get("witnesses", []))
        if witness_count > 0:
            score += min(5, witness_count)
        
        # Metadata completeness
        required_fields = ["title", "date", "committee_code", "url"]
        completeness = sum(1 for field in required_fields if hearing_data.get(field))
        score += completeness * 2
        
        return score
    
    def _apply_diversity_filters(self, candidates: List[Dict], target_count: int) -> List[Dict]:
        """Apply diversity filters to ensure varied test cases"""
        diverse_candidates = []
        committee_counts = {}
        audio_source_counts = {}
        
        # Ensure committee diversity
        max_per_committee = max(2, target_count // 5)  # At least 2 per committee, distributed
        
        # First pass - select best from each committee
        committee_groups = {}
        for candidate in candidates:
            committee = candidate["committee_code"]
            if committee not in committee_groups:
                committee_groups[committee] = []
            committee_groups[committee].append(candidate)
        
        # Select top candidates from each committee
        for committee, committee_candidates in committee_groups.items():
            committee_candidates.sort(key=lambda x: x["priority_score"], reverse=True)
            selected_count = min(max_per_committee, len(committee_candidates))
            
            for i in range(selected_count):
                if len(diverse_candidates) < target_count:
                    diverse_candidates.append(committee_candidates[i])
                    committee_counts[committee] = committee_counts.get(committee, 0) + 1
        
        # Second pass - fill remaining slots with highest scoring candidates
        remaining_candidates = [c for c in candidates if c not in diverse_candidates]
        remaining_candidates.sort(key=lambda x: x["priority_score"], reverse=True)
        
        for candidate in remaining_candidates:
            if len(diverse_candidates) >= target_count:
                break
            
            committee = candidate["committee_code"]
            audio_source = candidate["audio_source"]
            
            # Check diversity constraints
            committee_limit_ok = committee_counts.get(committee, 0) < max_per_committee + 1
            audio_variety_ok = audio_source_counts.get(audio_source, 0) < target_count // 2
            
            if committee_limit_ok and audio_variety_ok:
                diverse_candidates.append(candidate)
                committee_counts[committee] = committee_counts.get(committee, 0) + 1
                audio_source_counts[audio_source] = audio_source_counts.get(audio_source, 0) + 1
        
        return diverse_candidates[:target_count]
    
    def _generate_selection_rationale(self, hearing_data: Dict, candidate: Dict) -> str:
        """Generate rationale for hearing selection"""
        reasons = []
        
        # Readiness level
        score = candidate.get("score", 0)
        if score >= 0.8:
            reasons.append("Excellent readiness score")
        elif score >= 0.6:
            reasons.append("Good readiness score")
        
        # Audio source
        audio_source = candidate.get("audio_source", "None")
        if audio_source == "ISVP":
            reasons.append("ISVP streaming available")
        elif audio_source == "YouTube":
            reasons.append("YouTube backup available")
        
        # Committee priority
        committee_code = candidate.get("committee", "")
        if committee_code in ["SCOM", "SSCI", "SBAN", "SSJU"]:
            reasons.append("High-priority ISVP-compatible committee")
        
        # Metadata completeness
        if hearing_data.get("witnesses"):
            reasons.append("Witness information available")
        
        date_str = hearing_data.get("date")
        if date_str and "2025" in date_str:
            reasons.append("Recent hearing date")
        
        return "; ".join(reasons) if reasons else "Basic criteria met"
    
    def generate_testing_plan(self, priority_hearings: List[Dict]) -> Dict:
        """Generate testing plan for priority hearings"""
        logger.info("Generating testing plan...")
        
        testing_plan = {
            "plan_date": datetime.now().isoformat(),
            "total_hearings": len(priority_hearings),
            "testing_phases": [],
            "committee_distribution": {},
            "audio_source_distribution": {},
            "estimated_testing_time": 0,
            "success_rate_prediction": 0.0
        }
        
        # Analyze distribution
        committee_counts = {}
        audio_source_counts = {}
        readiness_scores = []
        
        for hearing in priority_hearings:
            committee = hearing["committee_code"]
            audio_source = hearing["audio_source"]
            
            committee_counts[committee] = committee_counts.get(committee, 0) + 1
            audio_source_counts[audio_source] = audio_source_counts.get(audio_source, 0) + 1
            readiness_scores.append(hearing["readiness_score"])
        
        testing_plan["committee_distribution"] = committee_counts
        testing_plan["audio_source_distribution"] = audio_source_counts
        
        # Create testing phases
        phases = self._create_testing_phases(priority_hearings)
        testing_plan["testing_phases"] = phases
        
        # Calculate estimated testing time (assuming 2 hours per hearing including analysis)
        testing_plan["estimated_testing_time"] = len(priority_hearings) * 120  # minutes
        
        # Predict success rate based on readiness scores
        if readiness_scores:
            avg_readiness = statistics.mean(readiness_scores)
            testing_plan["success_rate_prediction"] = min(0.95, avg_readiness + 0.1)
        
        return testing_plan
    
    def _create_testing_phases(self, priority_hearings: List[Dict]) -> List[Dict]:
        """Create testing phases for systematic validation"""
        phases = []
        
        # Phase 1: ISVP High-Priority (immediate validation)
        isvp_hearings = [h for h in priority_hearings if h["isvp_compatible"]]
        if isvp_hearings:
            phases.append({
                "phase": 1,
                "name": "ISVP High-Priority Validation",
                "description": "Test highest-priority ISVP-compatible hearings",
                "hearings": isvp_hearings[:5],
                "estimated_time": len(isvp_hearings[:5]) * 120,
                "success_criteria": "90% successful processing"
            })
        
        # Phase 2: Committee Diversity Test
        committee_samples = {}
        for hearing in priority_hearings:
            committee = hearing["committee_code"]
            if committee not in committee_samples:
                committee_samples[committee] = hearing
        
        diversity_hearings = list(committee_samples.values())[:8]
        if diversity_hearings:
            phases.append({
                "phase": 2,
                "name": "Committee Diversity Test",
                "description": "Validate processing across different committees",
                "hearings": diversity_hearings,
                "estimated_time": len(diversity_hearings) * 120,
                "success_criteria": "80% successful processing across all committees"
            })
        
        # Phase 3: Audio Source Validation
        youtube_hearings = [h for h in priority_hearings if h["audio_source"] == "YouTube"][:3]
        mixed_hearings = [h for h in priority_hearings if h["audio_source"] not in ["ISVP", "YouTube"]][:2]
        
        audio_test_hearings = youtube_hearings + mixed_hearings
        if audio_test_hearings:
            phases.append({
                "phase": 3,
                "name": "Audio Source Validation",
                "description": "Test different audio source types",
                "hearings": audio_test_hearings,
                "estimated_time": len(audio_test_hearings) * 120,
                "success_criteria": "70% successful processing for non-ISVP sources"
            })
        
        # Phase 4: Edge Case Testing
        remaining_hearings = [h for h in priority_hearings 
                            if h not in phases[0]["hearings"] + 
                               phases[1]["hearings"] + 
                               (phases[2]["hearings"] if len(phases) > 2 else [])]
        
        if remaining_hearings:
            phases.append({
                "phase": 4,
                "name": "Edge Case and Optimization",
                "description": "Test edge cases and optimize processing",
                "hearings": remaining_hearings,
                "estimated_time": len(remaining_hearings) * 120,
                "success_criteria": "Identify and resolve edge cases"
            })
        
        return phases
    
    def save_priority_list(self, priority_hearings: List[Dict], testing_plan: Dict, 
                          output_file: str = "priority_hearings.json"):
        """Save priority hearing list and testing plan"""
        output_path = self.catalog_file.parent / output_file
        
        output_data = {
            "generation_date": datetime.now().isoformat(),
            "total_priority_hearings": len(priority_hearings),
            "selection_criteria": self.priority_criteria,
            "target_committees": self.target_committees,
            "priority_hearings": priority_hearings,
            "testing_plan": testing_plan
        }
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Priority list saved to {output_path}")
        return output_path

def main():
    """Main priority selection function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Priority Hearing List")
    parser.add_argument("--catalog", default="data/hearings/hearing_catalog.json",
                       help="Hearing catalog file")
    parser.add_argument("--readiness", default="data/hearings/hearing_readiness_report.json",
                       help="Readiness report file")
    parser.add_argument("--count", type=int, default=20,
                       help="Number of priority hearings to select")
    parser.add_argument("--output", default="priority_hearings.json",
                       help="Output priority list file")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize selector
    selector = PriorityHearingSelector(args.catalog, args.readiness)
    
    # Select priority hearings
    priority_hearings = selector.select_priority_hearings(args.count)
    
    # Generate testing plan
    testing_plan = selector.generate_testing_plan(priority_hearings)
    
    # Save results
    output_file = selector.save_priority_list(priority_hearings, testing_plan, args.output)
    
    # Print summary
    print("\n" + "="*60)
    print("PRIORITY HEARING SELECTION COMPLETE")
    print("="*60)
    print(f"Selected Hearings: {len(priority_hearings)}")
    print(f"Testing Phases: {len(testing_plan['testing_phases'])}")
    print(f"Estimated Testing Time: {testing_plan['estimated_testing_time']//60:.1f} hours")
    print(f"Predicted Success Rate: {testing_plan['success_rate_prediction']:.1%}")
    
    print("\nCommittee Distribution:")
    for committee, count in testing_plan['committee_distribution'].items():
        committee_name = selector.target_committees.get(committee, {}).get("name", committee)
        print(f"  {committee} ({committee_name[:30]}): {count}")
    
    print("\nAudio Source Distribution:")
    for source, count in testing_plan['audio_source_distribution'].items():
        print(f"  {source}: {count}")
    
    print("\nTesting Phases:")
    for phase in testing_plan['testing_phases']:
        print(f"  Phase {phase['phase']}: {phase['name']} ({len(phase['hearings'])} hearings)")
    
    print(f"\nPriority list saved to: {output_file}")
    print("="*60)

if __name__ == "__main__":
    main()