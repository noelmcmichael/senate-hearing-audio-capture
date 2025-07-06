#!/usr/bin/env python3
"""
Test React progress components integration.
"""

import requests
import time
import json
from pathlib import Path

def test_react_progress_components():
    """Test the React progress components with chunked processing."""
    
    api_base = "http://localhost:8001"
    frontend_base = "http://localhost:3000"
    
    print("🧪 Testing React Progress Components Integration")
    print("=" * 60)
    
    # Test 1: Check if API server is running
    print("\n1. Checking API server availability...")
    try:
        response = requests.get(f"{api_base}/api/hearings", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running")
        else:
            print(f"❌ API server returned {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ API server not available: {e}")
        return False
    
    # Test 2: Check if frontend server is running
    print("\n2. Checking frontend server availability...")
    try:
        response = requests.get(frontend_base, timeout=5)
        if response.status_code == 200:
            print("✅ Frontend server is running")
        else:
            print(f"❌ Frontend server returned {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend server not available: {e}")
        print("   Please run: cd dashboard && npm start")
        return False
    
    # Test 3: Find a hearing for testing
    print("\n3. Finding hearing for testing...")
    hearings_response = requests.get(f"{api_base}/api/hearings")
    
    if hearings_response.status_code != 200:
        print("❌ Failed to get hearings list")
        return False
    
    hearings = hearings_response.json().get('hearings', [])
    captured_hearing = None
    
    for hearing in hearings:
        if hearing.get('processing_stage') == 'captured':
            captured_hearing = hearing
            break
    
    if not captured_hearing:
        print("⚠️  No hearing in 'captured' stage found")
        print("   Creating test scenario with available hearings...")
        
        # Find any hearing to demonstrate progress tracking
        if hearings:
            captured_hearing = hearings[0]
            print(f"📋 Using hearing {captured_hearing['id']}: {captured_hearing['hearing_title'][:50]}...")
        else:
            print("❌ No hearings available for testing")
            return False
    else:
        print(f"📋 Found captured hearing {captured_hearing['id']}: {captured_hearing['hearing_title'][:50]}...")
    
    hearing_id = captured_hearing['id']
    
    # Test 4: Test progress API endpoint structure
    print("\n4. Testing enhanced progress API structure...")
    progress_response = requests.get(f"{api_base}/api/hearings/{hearing_id}/transcription/progress")
    
    if progress_response.status_code != 200:
        print(f"❌ Progress API failed: {progress_response.status_code}")
        return False
    
    progress_data = progress_response.json()
    
    # Validate API response structure
    required_fields = ['success', 'hearing_id', 'hearing_title', 'detailed_progress']
    missing_fields = [field for field in required_fields if field not in progress_data]
    
    if missing_fields:
        print(f"❌ Missing required fields in API response: {missing_fields}")
        return False
    
    print("✅ Progress API structure is correct")
    
    # Validate detailed_progress structure
    detailed_progress = progress_data.get('detailed_progress', {})
    detailed_required = ['stage', 'overall_progress', 'message', 'is_chunked_processing']
    detailed_missing = [field for field in detailed_required if field not in detailed_progress]
    
    if detailed_missing:
        print(f"❌ Missing detailed_progress fields: {detailed_missing}")
        return False
    
    print("✅ Detailed progress structure is correct")
    print(f"   Current stage: {detailed_progress['stage']}")
    print(f"   Progress: {detailed_progress['overall_progress']}%")
    print(f"   Is chunked: {detailed_progress['is_chunked_processing']}")
    
    # Test 5: Component file existence
    print("\n5. Checking React component files...")
    
    component_files = [
        'dashboard/src/components/ChunkedProgressIndicator.js',
        'dashboard/src/components/ChunkedProgressIndicator.css'
    ]
    
    for file_path in component_files:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            return False
    
    # Test 6: PipelineControls integration
    print("\n6. Checking PipelineControls integration...")
    
    pipeline_controls_path = Path(__file__).parent / 'dashboard/src/components/PipelineControls.js'
    if not pipeline_controls_path.exists():
        print("❌ PipelineControls.js not found")
        return False
    
    with open(pipeline_controls_path, 'r') as f:
        pipeline_content = f.read()
    
    # Check for ChunkedProgressIndicator import
    if 'ChunkedProgressIndicator' in pipeline_content:
        print("✅ ChunkedProgressIndicator import found in PipelineControls")
    else:
        print("❌ ChunkedProgressIndicator import missing in PipelineControls")
        return False
    
    # Check for showProgressIndicator state
    if 'showProgressIndicator' in pipeline_content:
        print("✅ showProgressIndicator state found in PipelineControls")
    else:
        print("❌ showProgressIndicator state missing in PipelineControls")
        return False
    
    # Test 7: Manual UI testing instructions
    print("\n7. Manual UI testing instructions...")
    print("   📱 Frontend Integration Test Steps:")
    print(f"   1. Open: {frontend_base}")
    print(f"   2. Navigate to hearing: {captured_hearing['hearing_title'][:50]}")
    print("   3. Click 'Transcribe' button to start transcription")
    print("   4. Verify chunked progress indicator appears")
    print("   5. Monitor real-time progress updates")
    print("   6. Check chunk grid visualization (if chunked processing)")
    print("   7. Verify completion handling")
    
    # Test 8: Frontend build check
    print("\n8. Checking frontend build readiness...")
    
    package_json_path = Path(__file__).parent / 'dashboard/package.json'
    if package_json_path.exists():
        print("✅ package.json found")
        
        # Check if dependencies are installed
        node_modules_path = Path(__file__).parent / 'dashboard/node_modules'
        if node_modules_path.exists():
            print("✅ node_modules directory exists")
        else:
            print("⚠️  node_modules missing - run: cd dashboard && npm install")
    else:
        print("❌ package.json not found")
        return False
    
    print("\n" + "=" * 60)
    print("🎯 React Progress Components Test Summary:")
    print("   - API server: ✅ Available")
    print("   - Frontend server: ✅ Available") 
    print("   - Progress API: ✅ Enhanced structure")
    print("   - Component files: ✅ Created")
    print("   - PipelineControls: ✅ Integrated")
    print("   - Build readiness: ✅ Ready")
    
    print("\n📋 Next Steps:")
    print("   1. Start frontend: cd dashboard && npm start")
    print("   2. Test transcription with chunked progress")
    print("   3. Validate real-time progress updates")
    print("   4. Check responsive design on different screen sizes")
    
    return True

if __name__ == "__main__":
    success = test_react_progress_components()
    
    if success:
        print("\n✅ React Progress Components Test PASSED")
    else:
        print("\n❌ React Progress Components Test FAILED")
        exit(1)