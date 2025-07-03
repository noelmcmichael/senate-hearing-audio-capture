#!/usr/bin/env python3
"""
Comprehensive Audit - Check all transcripts and hearing statuses
"""

import json
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

class SystemAuditor:
    def __init__(self):
        self.db_path = Path('data/demo_enhanced_ui.db')
        self.transcript_dir = Path('output/demo_transcription')
        self.results = {
            'database_status': {},
            'transcript_quality': {},
            'mismatches': [],
            'issues': [],
            'recommendations': []
        }
    
    def audit_database_status(self):
        """Audit database hearing statuses"""
        print("🔍 Auditing Database Status...")
        
        conn = sqlite3.connect(str(self.db_path))
        
        # Get status distribution
        query = """
        SELECT 
            status,
            processing_stage,
            COUNT(*) as count
        FROM hearings_unified 
        GROUP BY status, processing_stage
        ORDER BY status, processing_stage;
        """
        
        df = pd.read_sql_query(query, conn)
        print("\nStatus Distribution:")
        print(df.to_string(index=False))
        
        # Get detailed hearing info
        detailed_query = """
        SELECT 
            id,
            hearing_title,
            committee_code,
            status,
            processing_stage,
            status_updated_at
        FROM hearings_unified 
        ORDER BY id;
        """
        
        detailed_df = pd.read_sql_query(detailed_query, conn)
        
        self.results['database_status'] = {
            'total_hearings': len(detailed_df),
            'status_distribution': df.to_dict('records'),
            'detailed_hearings': detailed_df.to_dict('records')
        }
        
        conn.close()
        
        # Summary stats
        complete_count = df[df['status'] == 'complete']['count'].sum()
        processing_count = df[df['status'] == 'processing']['count'].sum()
        
        print(f"\n📊 Database Summary:")
        print(f"   Total hearings: {len(detailed_df)}")
        print(f"   Complete: {complete_count}")
        print(f"   Processing: {processing_count}")
        
        return detailed_df
    
    def audit_transcript_quality(self):
        """Audit all transcript files for quality"""
        print("\n🔍 Auditing Transcript Quality...")
        
        transcript_files = list(self.transcript_dir.glob('hearing_*_transcript.json'))
        
        quality_results = []
        issues = []
        
        for file in transcript_files:
            try:
                with open(file) as f:
                    data = json.load(f)
                
                hearing_id = data.get('hearing_id')
                title = data.get('title', 'Unknown')
                committee = data.get('committee', 'Unknown')
                segments = data.get('segments', [])
                confidence = data.get('confidence', 0)
                
                # Calculate quality metrics
                total_duration = segments[-1].get('end', 0) if segments else 0
                avg_segment_duration = sum(seg.get('end', 0) - seg.get('start', 0) for seg in segments) / len(segments) if segments else 0
                speaker_diversity = len(set(seg.get('speaker', 'Unknown') for seg in segments))
                
                # Check for timeline gaps
                timeline_gaps = []
                for i in range(len(segments) - 1):
                    current_end = segments[i].get('end', 0)
                    next_start = segments[i+1].get('start', 0)
                    gap = next_start - current_end
                    if gap > 30:  # Gap longer than 30 seconds
                        timeline_gaps.append({
                            'segment': i,
                            'gap_seconds': gap,
                            'from_time': current_end,
                            'to_time': next_start
                        })
                
                # Quality assessment
                quality_score = 0
                if len(segments) >= 15:
                    quality_score += 30
                if total_duration >= 600:  # 10+ minutes
                    quality_score += 30
                if confidence >= 0.8:
                    quality_score += 20
                if speaker_diversity >= 3:
                    quality_score += 20
                
                quality_rating = "Excellent" if quality_score >= 90 else "Good" if quality_score >= 70 else "Fair" if quality_score >= 50 else "Poor"
                
                result = {
                    'hearing_id': hearing_id,
                    'title': title[:40] + '...' if len(title) > 40 else title,
                    'committee': committee,
                    'segments': len(segments),
                    'duration_seconds': total_duration,
                    'duration_minutes': round(total_duration / 60, 1),
                    'confidence': confidence,
                    'speaker_diversity': speaker_diversity,
                    'timeline_gaps': len(timeline_gaps),
                    'quality_score': quality_score,
                    'quality_rating': quality_rating,
                    'file_size': file.stat().st_size
                }
                
                quality_results.append(result)
                
                # Flag issues
                if timeline_gaps:
                    issues.append({
                        'hearing_id': hearing_id,
                        'issue': 'Timeline gaps detected',
                        'details': f"{len(timeline_gaps)} gaps found, largest: {max(g['gap_seconds'] for g in timeline_gaps)}s"
                    })
                
                if len(segments) < 10:
                    issues.append({
                        'hearing_id': hearing_id,
                        'issue': 'Low segment count',
                        'details': f"Only {len(segments)} segments"
                    })
                
                if total_duration < 300:  # Less than 5 minutes
                    issues.append({
                        'hearing_id': hearing_id,
                        'issue': 'Short duration',
                        'details': f"Only {round(total_duration/60, 1)} minutes"
                    })
                
            except Exception as e:
                issues.append({
                    'hearing_id': 'Unknown',
                    'issue': 'File read error',
                    'details': f"Error reading {file.name}: {e}"
                })
        
        # Sort by quality score
        quality_results.sort(key=lambda x: x['quality_score'], reverse=True)
        
        self.results['transcript_quality'] = {
            'total_files': len(transcript_files),
            'quality_results': quality_results,
            'issues': issues
        }
        
        # Print summary
        print(f"\n📊 Transcript Quality Summary:")
        print(f"   Total files: {len(transcript_files)}")
        print(f"   Issues found: {len(issues)}")
        
        ratings = {}
        for result in quality_results:
            rating = result['quality_rating']
            ratings[rating] = ratings.get(rating, 0) + 1
        
        print(f"   Quality ratings: {ratings}")
        
        return quality_results, issues
    
    def cross_reference_status(self, db_hearings, transcript_results):
        """Cross-reference database status with transcript availability"""
        print("\n🔍 Cross-Referencing Status...")
        
        # Create lookup dicts
        db_lookup = {h['id']: h for h in db_hearings}
        transcript_lookup = {t['hearing_id']: t for t in transcript_results}
        
        mismatches = []
        
        for hearing_id, db_hearing in db_lookup.items():
            status = db_hearing['status']
            stage = db_hearing['processing_stage']
            
            if status == 'complete' and stage == 'published':
                # Should have quality transcript
                if hearing_id not in transcript_lookup:
                    mismatches.append({
                        'hearing_id': hearing_id,
                        'issue': 'Complete hearing missing transcript',
                        'db_status': f"{status}/{stage}",
                        'transcript_status': 'Missing'
                    })
                else:
                    transcript = transcript_lookup[hearing_id]
                    if transcript['quality_rating'] in ['Poor', 'Fair']:
                        mismatches.append({
                            'hearing_id': hearing_id,
                            'issue': 'Complete hearing has poor transcript',
                            'db_status': f"{status}/{stage}",
                            'transcript_status': f"{transcript['quality_rating']} ({transcript['segments']} segments)"
                        })
        
        # Check for transcripts without matching database entries
        for hearing_id, transcript in transcript_lookup.items():
            if hearing_id not in db_lookup:
                mismatches.append({
                    'hearing_id': hearing_id,
                    'issue': 'Transcript without database entry',
                    'db_status': 'Missing',
                    'transcript_status': f"{transcript['quality_rating']} ({transcript['segments']} segments)"
                })
        
        self.results['mismatches'] = mismatches
        
        print(f"   Status mismatches: {len(mismatches)}")
        
        return mismatches
    
    def generate_recommendations(self):
        """Generate recommendations based on audit results"""
        print("\n🔍 Generating Recommendations...")
        
        recommendations = []
        
        # Check for issues
        transcript_issues = self.results['transcript_quality']['issues']
        mismatches = self.results['mismatches']
        
        if transcript_issues:
            recommendations.append({
                'priority': 'High',
                'action': 'Fix transcript quality issues',
                'details': f"{len(transcript_issues)} transcripts have quality issues",
                'hearings_affected': [issue['hearing_id'] for issue in transcript_issues]
            })
        
        if mismatches:
            recommendations.append({
                'priority': 'Medium',
                'action': 'Resolve status mismatches',
                'details': f"{len(mismatches)} status/transcript mismatches found",
                'hearings_affected': [m['hearing_id'] for m in mismatches]
            })
        
        # Check for low-quality transcripts
        quality_results = self.results['transcript_quality']['quality_results']
        poor_quality = [r for r in quality_results if r['quality_rating'] in ['Poor', 'Fair']]
        
        if poor_quality:
            recommendations.append({
                'priority': 'Medium',
                'action': 'Improve low-quality transcripts',
                'details': f"{len(poor_quality)} transcripts need quality improvement",
                'hearings_affected': [r['hearing_id'] for r in poor_quality]
            })
        
        self.results['recommendations'] = recommendations
        
        return recommendations
    
    def print_detailed_report(self):
        """Print comprehensive audit report"""
        print("\n" + "="*80)
        print("📋 COMPREHENSIVE AUDIT REPORT")
        print("="*80)
        
        # Database status
        print(f"\n📊 Database Status:")
        for status in self.results['database_status']['status_distribution']:
            print(f"   {status['status']}/{status['processing_stage']}: {status['count']} hearings")
        
        # Transcript quality
        print(f"\n📊 Transcript Quality:")
        quality_results = self.results['transcript_quality']['quality_results']
        print(f"   Total files: {len(quality_results)}")
        
        # Quality distribution
        ratings = {}
        for result in quality_results:
            rating = result['quality_rating']
            ratings[rating] = ratings.get(rating, 0) + 1
        
        for rating, count in ratings.items():
            print(f"   {rating}: {count} transcripts")
        
        # Issues
        issues = self.results['transcript_quality']['issues']
        if issues:
            print(f"\n⚠️  Issues Found ({len(issues)}):")
            for issue in issues[:10]:  # Show first 10
                print(f"   Hearing {issue['hearing_id']}: {issue['issue']} - {issue['details']}")
            if len(issues) > 10:
                print(f"   ... and {len(issues) - 10} more issues")
        
        # Mismatches
        mismatches = self.results['mismatches']
        if mismatches:
            print(f"\n⚠️  Status Mismatches ({len(mismatches)}):")
            for mismatch in mismatches[:5]:  # Show first 5
                print(f"   Hearing {mismatch['hearing_id']}: {mismatch['issue']}")
            if len(mismatches) > 5:
                print(f"   ... and {len(mismatches) - 5} more mismatches")
        
        # Recommendations
        recommendations = self.results['recommendations']
        if recommendations:
            print(f"\n🎯 Recommendations ({len(recommendations)}):")
            for rec in recommendations:
                print(f"   [{rec['priority']}] {rec['action']}: {rec['details']}")
        
        # Summary
        print(f"\n✅ Audit Complete:")
        print(f"   Total hearings: {self.results['database_status']['total_hearings']}")
        print(f"   Total transcripts: {len(quality_results)}")
        print(f"   Issues found: {len(issues)}")
        print(f"   Status mismatches: {len(mismatches)}")
        print(f"   Recommendations: {len(recommendations)}")
        
        return self.results
    
    def run_full_audit(self):
        """Run complete audit process"""
        print("🔍 Starting Comprehensive System Audit...")
        
        # Step 1: Database audit
        db_hearings = self.audit_database_status()
        
        # Step 2: Transcript quality audit
        transcript_results, transcript_issues = self.audit_transcript_quality()
        
        # Step 3: Cross-reference
        mismatches = self.cross_reference_status(db_hearings.to_dict('records'), transcript_results)
        
        # Step 4: Generate recommendations
        recommendations = self.generate_recommendations()
        
        # Step 5: Print report
        return self.print_detailed_report()

if __name__ == "__main__":
    auditor = SystemAuditor()
    results = auditor.run_full_audit()