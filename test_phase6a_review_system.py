#!/usr/bin/env python3
"""
Test Phase 6A: Human Review System

Tests the complete review workflow:
1. Review API functionality 
2. Correction storage
3. Transcript preparation and export
4. React frontend integration
"""

import sys
import json
import time
import asyncio
import subprocess
import threading
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from review.review_api import create_app
from review.correction_store import CorrectionStore
from review.review_utils import ReviewUtils


class Phase6ATestSuite:
    """Comprehensive test suite for Phase 6A review system."""
    
    def __init__(self):
        self.test_results = []
        self.app = create_app()
        self.correction_store = CorrectionStore()
        self.review_utils = ReviewUtils()
        
    def run_all_tests(self):
        """Run all Phase 6A tests."""
        print("🚀 Phase 6A Test Suite: Human Review System")
        print("=" * 60)
        
        tests = [
            self.test_correction_store,
            self.test_review_utils,
            self.test_api_endpoints,
            self.test_complete_workflow,
            self.test_frontend_integration
        ]
        
        for test in tests:
            try:
                print(f"\n🧪 Running {test.__name__}...")
                result = test()
                self.test_results.append({
                    "test": test.__name__,
                    "status": "PASS" if result else "FAIL",
                    "details": result if isinstance(result, dict) else {}
                })
                print(f"✅ {test.__name__}: PASS")
            except Exception as e:
                print(f"❌ {test.__name__}: FAIL - {e}")
                self.test_results.append({
                    "test": test.__name__,
                    "status": "FAIL",
                    "error": str(e)
                })
        
        self.print_summary()
    
    def test_correction_store(self):
        """Test SQLite correction storage functionality."""
        print("  Testing correction storage...")
        
        # Test save correction
        correction_id = self.correction_store.save_correction(
            transcript_file="test_transcript.json",
            segment_id=1,
            speaker_name="Sen. Cruz",
            confidence=0.95,
            reviewer_id="test_reviewer"
        )
        
        assert correction_id is not None
        print(f"    ✓ Saved correction: {correction_id}")
        
        # Test get corrections
        corrections = self.correction_store.get_corrections("test_transcript.json")
        assert len(corrections) == 1
        assert corrections[0]["speaker_name"] == "Sen. Cruz"
        print(f"    ✓ Retrieved {len(corrections)} corrections")
        
        # Test correction stats
        stats = self.correction_store.get_correction_stats("test_transcript.json")
        assert stats["total_corrections"] == 1
        assert stats["unique_speakers"] == 1
        print(f"    ✓ Stats: {stats['total_corrections']} corrections")
        
        # Test bulk corrections
        for i in range(2, 5):
            self.correction_store.save_correction(
                transcript_file="test_transcript.json",
                segment_id=i,
                speaker_name="Sen. Warren",
                confidence=0.9,
                reviewer_id="test_reviewer"
            )
        
        updated_stats = self.correction_store.get_correction_stats("test_transcript.json")
        assert updated_stats["total_corrections"] == 4
        print(f"    ✓ Bulk corrections: {updated_stats['total_corrections']} total")
        
        return True
    
    def test_review_utils(self):
        """Test review utilities for transcript preparation."""
        print("  Testing review utilities...")
        
        # Create test transcript
        test_transcript = {
            "transcription": {
                "segments": [
                    {
                        "id": 0,
                        "start": 0.0,
                        "end": 5.0,
                        "text": "Thank you Mr. Chairman",
                        "confidence": "low"
                    },
                    {
                        "id": 1,
                        "start": 5.0,
                        "end": 10.0,
                        "text": "I yield the floor to Senator Cruz",
                        "confidence": "high",
                        "speaker": "Chair"
                    }
                ]
            },
            "enrichment": {
                "committee_members": [
                    {"name": "Ted Cruz", "display_name": "Sen. Cruz"},
                    {"name": "Elizabeth Warren", "display_name": "Sen. Warren"}
                ]
            }
        }
        
        # Test prepare for review
        enhanced = self.review_utils.prepare_for_review(test_transcript)
        
        assert "review_metadata" in enhanced
        assert enhanced["review_metadata"]["total_segments"] == 2
        print(f"    ✓ Enhanced transcript with {enhanced['review_metadata']['total_segments']} segments")
        
        # Check segment enhancement
        segments = enhanced["transcription"]["segments"]
        assert "review_metadata" in segments[0]
        assert segments[0]["review_metadata"]["needs_review"] == True  # Low confidence
        assert segments[1]["review_metadata"]["needs_review"] == False  # Has speaker
        print(f"    ✓ Segment review flags: {sum(s['review_metadata']['needs_review'] for s in segments)} need review")
        
        # Test apply corrections
        test_corrections = [
            {
                "id": "test-1",
                "segment_id": 0,
                "speaker_name": "Sen. Warren",
                "confidence": 0.9,
                "reviewer_id": "test_reviewer",
                "created_at": "2024-01-01T10:00:00"
            }
        ]
        
        corrected = self.review_utils.apply_corrections(test_transcript, test_corrections)
        
        corrected_segments = corrected["transcription"]["segments"]
        assert corrected_segments[0]["speaker"] == "Sen. Warren"
        assert corrected_segments[0]["corrected"] == True
        print("    ✓ Applied corrections successfully")
        
        return True
    
    def test_api_endpoints(self):
        """Test FastAPI endpoints using test client."""
        print("  Testing API endpoints...")
        
        from fastapi.testclient import TestClient
        client = TestClient(self.app)
        
        # Test health check
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        print("    ✓ Health check endpoint")
        
        # Test list transcripts (will be empty for now)
        response = client.get("/transcripts")
        assert response.status_code == 200
        data = response.json()
        assert "transcripts" in data
        print(f"    ✓ List transcripts: {len(data['transcripts'])} found")
        
        return True
    
    def test_complete_workflow(self):
        """Test complete review workflow with real transcript data."""
        print("  Testing complete review workflow...")
        
        # Check if demo transcript exists
        demo_transcript_path = Path("output/demo_transcription/senate_hearing_20250627_123720_stream1_complete_transcript.json")
        
        if demo_transcript_path.exists():
            print(f"    ✓ Found demo transcript: {demo_transcript_path.name}")
            
            # Load transcript
            with open(demo_transcript_path, 'r') as f:
                transcript_data = json.load(f)
            
            # Test enhancement
            enhanced = self.review_utils.prepare_for_review(transcript_data)
            print(f"    ✓ Enhanced transcript: {enhanced['review_metadata']['total_segments']} segments")
            
            # Test correction storage for real transcript
            correction_id = self.correction_store.save_correction(
                transcript_file=str(demo_transcript_path),
                segment_id=0,
                speaker_name="Sen. Cruz",
                confidence=0.95,
                reviewer_id="workflow_test"
            )
            print(f"    ✓ Saved real transcript correction: {correction_id}")
            
            # Test export
            corrections = self.correction_store.get_corrections(str(demo_transcript_path))
            corrected_transcript = self.review_utils.apply_corrections(transcript_data, corrections)
            
            export_path = demo_transcript_path.parent / f"{demo_transcript_path.stem}_test_export.json"
            with open(export_path, 'w') as f:
                json.dump(corrected_transcript, f, indent=2, default=str)
            
            print(f"    ✓ Exported corrected transcript: {export_path.name}")
            
        else:
            print("    ⚠️  No demo transcript found, skipping real data test")
        
        return True
    
    def test_frontend_integration(self):
        """Test React frontend integration readiness."""
        print("  Testing frontend integration...")
        
        # Check dashboard files exist
        dashboard_path = Path("dashboard")
        required_files = [
            "package.json",
            "src/App.js",
            "src/components/TranscriptViewer/TranscriptViewer.js"
        ]
        
        for file_path in required_files:
            full_path = dashboard_path / file_path
            assert full_path.exists(), f"Missing required file: {file_path}"
            print(f"    ✓ Found: {file_path}")
        
        # Check package.json for dependencies
        with open(dashboard_path / "package.json", 'r') as f:
            package_data = json.load(f)
        
        required_deps = ["react", "lucide-react"]
        for dep in required_deps:
            assert dep in package_data.get("dependencies", {}), f"Missing dependency: {dep}"
            print(f"    ✓ Dependency: {dep}")
        
        print("    ✓ Frontend integration ready")
        return True
    
    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 60)
        print("🏁 Phase 6A Test Results Summary")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        total = len(self.test_results)
        
        print(f"✅ Tests Passed: {passed}/{total}")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Phase 6A human review system is ready.")
            print("\nNext Steps:")
            print("1. Install FastAPI dependencies: uv pip install fastapi uvicorn pydantic")
            print("2. Start review API: python src/review/review_api.py")
            print("3. Start React dashboard: cd dashboard && npm start")
            print("4. Test with real transcript review workflow")
        else:
            print(f"\n❌ {total - passed} tests failed. Check errors above.")
            
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"   - {result['test']}: {result.get('error', 'Unknown error')}")
        
        return passed == total


def main():
    """Run Phase 6A test suite."""
    print("Phase 6A: Human Review System Test Suite")
    print("Testing transcript review workflow components...")
    
    test_suite = Phase6ATestSuite()
    test_suite.run_all_tests()


if __name__ == "__main__":
    main()