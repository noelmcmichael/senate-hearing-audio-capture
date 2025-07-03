#!/usr/bin/env python3
"""
Hearing Readiness Assessment System
Assesses hearing processing feasibility and generates recommendations
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
import statistics
from dataclasses import dataclass
import re

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ReadinessAssessment:
    """Hearing readiness assessment"""
    hearing_id: str
    title: str
    committee_code: str
    overall_score: float
    readiness_level: str  # "EXCELLENT", "GOOD", "FAIR", "POOR"
    processing_time_estimate: int  # minutes
    success_probability: float  # 0-1
    recommendations: List[str]
    blockers: List[str]
    audio_source: str  # "ISVP", "YouTube", "None"
    complexity_factors: Dict[str, float]
    priority_rank: int

class HearingReadinessAssessor:
    """Assesses hearing processing readiness"""
    
    def __init__(self, catalog_file: str = "data/hearings/hearing_catalog.json"):
        self.catalog_file = Path(catalog_file)
        self.hearings = self._load_hearings()
        
        # Assessment criteria weights
        self.criteria_weights = {
            "audio_availability": 0.30,
            "metadata_completeness": 0.20,
            "date_recency": 0.15,
            "content_quality": 0.15,
            "processing_complexity": 0.10,
            "isvp_compatibility": 0.10
        }
        
        # Processing time estimates (minutes)
        self.processing_times = {
            "audio_capture": 5,
            "preprocessing": 10,
            "whisper_transcription": 0.5,  # per minute of audio
            "speaker_identification": 15,
            "quality_review": 20,
            "final_processing": 5
        }
        
        # Success probability factors
        self.success_factors = {
            "has_isvp": 0.95,
            "has_youtube": 0.85,
            "has_date": 0.80,
            "has_witnesses": 0.75,
            "recent_date": 0.85,
            "complete_metadata": 0.90,
            "simple_committee": 0.85,
            "reasonable_duration": 0.90
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
    
    def assess_hearing(self, hearing_id: str, hearing_data: Dict) -> ReadinessAssessment:
        """Assess individual hearing readiness"""
        
        # Calculate component scores
        audio_score = self._assess_audio_availability(hearing_data)
        metadata_score = self._assess_metadata_completeness(hearing_data)
        date_score = self._assess_date_recency(hearing_data)
        content_score = self._assess_content_quality(hearing_data)
        complexity_score = self._assess_processing_complexity(hearing_data)
        isvp_score = self._assess_isvp_compatibility(hearing_data)
        
        # Calculate weighted overall score
        overall_score = (
            audio_score * self.criteria_weights["audio_availability"] +
            metadata_score * self.criteria_weights["metadata_completeness"] +
            date_score * self.criteria_weights["date_recency"] +
            content_score * self.criteria_weights["content_quality"] +
            complexity_score * self.criteria_weights["processing_complexity"] +
            isvp_score * self.criteria_weights["isvp_compatibility"]
        )
        
        # Determine readiness level
        readiness_level = self._determine_readiness_level(overall_score)
        
        # Estimate processing time
        processing_time = self._estimate_processing_time(hearing_data)
        
        # Calculate success probability
        success_probability = self._calculate_success_probability(hearing_data)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(hearing_data, overall_score)
        
        # Identify blockers
        blockers = self._identify_blockers(hearing_data)
        
        # Determine audio source
        audio_source = self._determine_audio_source(hearing_data)
        
        # Complexity factors
        complexity_factors = {
            "audio_availability": audio_score,
            "metadata_completeness": metadata_score,
            "date_recency": date_score,
            "content_quality": content_score,
            "processing_complexity": complexity_score,
            "isvp_compatibility": isvp_score
        }
        
        return ReadinessAssessment(
            hearing_id=hearing_id,
            title=hearing_data.get("title", "Unknown"),
            committee_code=hearing_data.get("committee_code", "Unknown"),
            overall_score=overall_score,
            readiness_level=readiness_level,
            processing_time_estimate=processing_time,
            success_probability=success_probability,
            recommendations=recommendations,
            blockers=blockers,
            audio_source=audio_source,
            complexity_factors=complexity_factors,
            priority_rank=0  # Will be set later
        )
    
    def _assess_audio_availability(self, hearing_data: Dict) -> float:
        """Assess audio availability"""
        score = 0.0
        
        if hearing_data.get("isvp_compatible"):
            score = 1.0
        elif hearing_data.get("youtube_url"):
            score = 0.8
        elif hearing_data.get("audio_available"):
            score = 0.6
        else:
            score = 0.0
        
        return score
    
    def _assess_metadata_completeness(self, hearing_data: Dict) -> float:
        """Assess metadata completeness"""
        required_fields = ["title", "date", "committee_code"]
        optional_fields = ["time", "location", "witnesses", "topics"]
        
        score = 0.0
        
        # Required fields (70% of score)
        required_score = 0.0
        for field in required_fields:
            if hearing_data.get(field):
                required_score += 1.0
        required_score = required_score / len(required_fields) * 0.7
        
        # Optional fields (30% of score)
        optional_score = 0.0
        for field in optional_fields:
            if hearing_data.get(field):
                optional_score += 1.0
        optional_score = optional_score / len(optional_fields) * 0.3
        
        score = required_score + optional_score
        return min(1.0, score)
    
    def _assess_date_recency(self, hearing_data: Dict) -> float:
        """Assess date recency"""
        date_str = hearing_data.get("date")
        if not date_str:
            return 0.0
        
        # Simple recency assessment - prioritize 2025 dates
        if "2025" in date_str:
            return 1.0
        elif "2024" in date_str:
            return 0.7
        else:
            return 0.3
    
    def _assess_content_quality(self, hearing_data: Dict) -> float:
        """Assess content quality"""
        score = 0.0
        
        # Title quality
        title = hearing_data.get("title", "")
        if len(title) > 20:
            score += 0.3
        elif len(title) > 10:
            score += 0.2
        
        # Witness availability
        witnesses = hearing_data.get("witnesses", [])
        if witnesses and len(witnesses) > 0:
            score += 0.3
        
        # Topic identification
        topics = hearing_data.get("topics", [])
        if topics and len(topics) > 0:
            score += 0.2
        
        # URL availability
        if hearing_data.get("url"):
            score += 0.2
        
        return min(1.0, score)
    
    def _assess_processing_complexity(self, hearing_data: Dict) -> float:
        """Assess processing complexity (higher score = simpler)"""
        score = 1.0
        
        # Committee complexity
        committee_code = hearing_data.get("committee_code", "")
        complex_committees = ["SAPP", "SFIN", "SFRC"]  # Appropriations, Finance, Foreign Relations
        if committee_code in complex_committees:
            score -= 0.2
        
        # Hearing type complexity
        hearing_type = hearing_data.get("hearing_type", "")
        if hearing_type in ["markup", "executive_session"]:
            score -= 0.1
        
        # Witness count complexity
        witness_count = hearing_data.get("witness_count", 0)
        if witness_count and isinstance(witness_count, int) and witness_count > 5:
            score -= 0.1
        
        # Title complexity
        title = hearing_data.get("title", "")
        if len(title) > 100:
            score -= 0.1
        
        return max(0.0, score)
    
    def _assess_isvp_compatibility(self, hearing_data: Dict) -> float:
        """Assess ISVP compatibility"""
        if hearing_data.get("isvp_compatible"):
            return 1.0
        elif hearing_data.get("isvp_url"):
            return 0.8
        else:
            return 0.0
    
    def _determine_readiness_level(self, overall_score: float) -> str:
        """Determine readiness level"""
        if overall_score >= 0.8:
            return "EXCELLENT"
        elif overall_score >= 0.6:
            return "GOOD"
        elif overall_score >= 0.4:
            return "FAIR"
        else:
            return "POOR"
    
    def _estimate_processing_time(self, hearing_data: Dict) -> int:
        """Estimate processing time in minutes"""
        base_time = (
            self.processing_times["audio_capture"] +
            self.processing_times["preprocessing"] +
            self.processing_times["speaker_identification"] +
            self.processing_times["quality_review"] +
            self.processing_times["final_processing"]
        )
        
        # Estimate audio duration (default 60 minutes)
        estimated_duration = 60
        if hearing_data.get("duration_estimate"):
            estimated_duration = hearing_data["duration_estimate"]
        
        # Transcription time
        transcription_time = estimated_duration * self.processing_times["whisper_transcription"]
        
        total_time = base_time + transcription_time
        
        # Complexity adjustments
        witness_count = hearing_data.get("witness_count", 0)
        if witness_count and witness_count > 5:
            total_time *= 1.3
        
        hearing_type = hearing_data.get("hearing_type")
        if hearing_type and hearing_type in ["markup", "executive_session"]:
            total_time *= 1.2
        
        return int(total_time)
    
    def _calculate_success_probability(self, hearing_data: Dict) -> float:
        """Calculate success probability"""
        probability = 0.5  # Base probability
        
        # Apply success factors
        if hearing_data.get("isvp_compatible"):
            probability *= self.success_factors["has_isvp"]
        elif hearing_data.get("youtube_url"):
            probability *= self.success_factors["has_youtube"]
        
        if hearing_data.get("date"):
            probability *= self.success_factors["has_date"]
        
        if hearing_data.get("witnesses"):
            probability *= self.success_factors["has_witnesses"]
        
        if hearing_data.get("date") and "2025" in hearing_data["date"]:
            probability *= self.success_factors["recent_date"]
        
        # Metadata completeness
        required_fields = ["title", "date", "committee_code"]
        if all(hearing_data.get(field) for field in required_fields):
            probability *= self.success_factors["complete_metadata"]
        
        return min(1.0, probability)
    
    def _generate_recommendations(self, hearing_data: Dict, overall_score: float) -> List[str]:
        """Generate processing recommendations"""
        recommendations = []
        
        # Audio source recommendations
        if not hearing_data.get("isvp_compatible") and not hearing_data.get("youtube_url"):
            recommendations.append("⚠️ No audio source detected - check for ISVP or YouTube availability")
        
        # Metadata recommendations
        if not hearing_data.get("date"):
            recommendations.append("📅 Missing date information - required for processing")
        
        if not hearing_data.get("witnesses"):
            recommendations.append("👥 No witnesses identified - may impact speaker identification")
        
        # Processing recommendations
        if overall_score >= 0.8:
            recommendations.append("🎯 High-priority candidate for immediate processing")
        elif overall_score >= 0.6:
            recommendations.append("✅ Good candidate for processing with minor preparations")
        elif overall_score >= 0.4:
            recommendations.append("⚠️ Requires preparation before processing")
        else:
            recommendations.append("❌ Not recommended for processing without significant improvements")
        
        # Committee-specific recommendations
        committee_code = hearing_data.get("committee_code", "")
        if committee_code in ["SCOM", "SSCI", "SBAN", "SSJU"]:
            recommendations.append("🔥 ISVP-compatible committee - high processing success rate")
        
        return recommendations
    
    def _identify_blockers(self, hearing_data: Dict) -> List[str]:
        """Identify processing blockers"""
        blockers = []
        
        # Critical blockers
        if not hearing_data.get("audio_available") and not hearing_data.get("isvp_compatible"):
            blockers.append("No audio source available")
        
        if not hearing_data.get("title"):
            blockers.append("Missing hearing title")
        
        if not hearing_data.get("committee_code"):
            blockers.append("Missing committee identification")
        
        # Warning blockers
        if hearing_data.get("status") == "cancelled":
            blockers.append("Hearing cancelled")
        
        if hearing_data.get("date") and "2023" in hearing_data["date"]:
            blockers.append("Very old hearing date")
        
        return blockers
    
    def _determine_audio_source(self, hearing_data: Dict) -> str:
        """Determine primary audio source"""
        if hearing_data.get("isvp_compatible"):
            return "ISVP"
        elif hearing_data.get("youtube_url"):
            return "YouTube"
        else:
            return "None"
    
    def assess_all_hearings(self) -> Dict[str, ReadinessAssessment]:
        """Assess all hearings in catalog"""
        logger.info("Assessing readiness for all hearings...")
        
        assessments = {}
        hearings = self.hearings.get("hearings", {})
        
        for hearing_id, hearing_data in hearings.items():
            assessment = self.assess_hearing(hearing_id, hearing_data)
            assessments[hearing_id] = assessment
        
        # Calculate priority ranks
        sorted_assessments = sorted(assessments.values(), 
                                  key=lambda x: x.overall_score, 
                                  reverse=True)
        
        for i, assessment in enumerate(sorted_assessments):
            assessment.priority_rank = i + 1
        
        logger.info(f"Assessed {len(assessments)} hearings")
        return assessments
    
    def generate_readiness_report(self, assessments: Dict[str, ReadinessAssessment]) -> Dict:
        """Generate comprehensive readiness report"""
        logger.info("Generating readiness report...")
        
        report = {
            "assessment_date": datetime.now().isoformat(),
            "total_hearings": len(assessments),
            "readiness_distribution": {},
            "audio_source_distribution": {},
            "processing_statistics": {},
            "recommendations": {
                "immediate_processing": [],
                "requires_preparation": [],
                "not_recommended": []
            }
        }
        
        # Calculate distributions
        readiness_counts = {}
        audio_source_counts = {}
        processing_times = []
        success_probabilities = []
        
        for assessment in assessments.values():
            # Readiness distribution
            level = assessment.readiness_level
            readiness_counts[level] = readiness_counts.get(level, 0) + 1
            
            # Audio source distribution
            source = assessment.audio_source
            audio_source_counts[source] = audio_source_counts.get(source, 0) + 1
            
            # Processing statistics
            processing_times.append(assessment.processing_time_estimate)
            success_probabilities.append(assessment.success_probability)
            
            # Categorize recommendations
            if assessment.overall_score >= 0.8:
                report["recommendations"]["immediate_processing"].append({
                    "hearing_id": assessment.hearing_id,
                    "title": assessment.title,
                    "committee": assessment.committee_code,
                    "score": assessment.overall_score,
                    "audio_source": assessment.audio_source
                })
            elif assessment.overall_score >= 0.4:
                report["recommendations"]["requires_preparation"].append({
                    "hearing_id": assessment.hearing_id,
                    "title": assessment.title,
                    "committee": assessment.committee_code,
                    "score": assessment.overall_score,
                    "blockers": assessment.blockers
                })
            else:
                report["recommendations"]["not_recommended"].append({
                    "hearing_id": assessment.hearing_id,
                    "title": assessment.title,
                    "committee": assessment.committee_code,
                    "score": assessment.overall_score,
                    "blockers": assessment.blockers
                })
        
        # Set distributions
        report["readiness_distribution"] = readiness_counts
        report["audio_source_distribution"] = audio_source_counts
        
        # Calculate processing statistics
        if processing_times:
            report["processing_statistics"] = {
                "avg_processing_time": statistics.mean(processing_times),
                "median_processing_time": statistics.median(processing_times),
                "total_processing_time": sum(processing_times),
                "avg_success_probability": statistics.mean(success_probabilities),
                "high_success_hearings": len([p for p in success_probabilities if p >= 0.8])
            }
        
        # Sort recommendations by score
        for category in report["recommendations"].values():
            if isinstance(category, list):
                category.sort(key=lambda x: x["score"], reverse=True)
        
        return report
    
    def save_readiness_report(self, report: Dict, output_file: str = "hearing_readiness_report.json"):
        """Save readiness report"""
        output_path = self.catalog_file.parent / output_file
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Readiness report saved to {output_path}")
        return output_path

def main():
    """Main readiness assessment function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Assess Hearing Processing Readiness")
    parser.add_argument("--catalog", default="data/hearings/hearing_catalog.json",
                       help="Hearing catalog file")
    parser.add_argument("--output", default="hearing_readiness_report.json",
                       help="Output report file")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize assessor
    assessor = HearingReadinessAssessor(args.catalog)
    
    # Assess all hearings
    assessments = assessor.assess_all_hearings()
    
    # Generate report
    report = assessor.generate_readiness_report(assessments)
    
    # Save report
    output_file = assessor.save_readiness_report(report, args.output)
    
    # Print summary
    print("\n" + "="*60)
    print("HEARING READINESS ASSESSMENT COMPLETE")
    print("="*60)
    print(f"Total Hearings Assessed: {report['total_hearings']}")
    print("\nReadiness Distribution:")
    for level, count in report['readiness_distribution'].items():
        print(f"  {level}: {count}")
    print("\nAudio Source Distribution:")
    for source, count in report['audio_source_distribution'].items():
        print(f"  {source}: {count}")
    print("\nProcessing Recommendations:")
    print(f"  Immediate Processing: {len(report['recommendations']['immediate_processing'])}")
    print(f"  Requires Preparation: {len(report['recommendations']['requires_preparation'])}")
    print(f"  Not Recommended: {len(report['recommendations']['not_recommended'])}")
    
    if report.get('processing_statistics'):
        stats = report['processing_statistics']
        print(f"\nProcessing Statistics:")
        print(f"  Average Processing Time: {stats['avg_processing_time']:.1f} minutes")
        print(f"  Average Success Probability: {stats['avg_success_probability']:.2f}")
        print(f"  High Success Hearings: {stats['high_success_hearings']}")
    
    print(f"\nReport saved to: {output_file}")
    print("="*60)

if __name__ == "__main__":
    main()