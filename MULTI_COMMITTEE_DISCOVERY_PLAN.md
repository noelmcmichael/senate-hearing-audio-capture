# Multi-Committee Discovery & Manual Processing Plan

## Executive Summary
Scale the validated system to discover hearings across all Senate committees and subcommittees, with manual processing controls for systematic testing and validation.

## Step-by-Step Implementation Plan

### Phase 1: Committee Discovery & Cataloging (30 minutes)
**Objective**: Discover all available hearings across committees and subcommittees

#### Step 1.1: Committee Structure Discovery (10 minutes)
- **Task**: Identify all Senate committees and their subcommittees
- **Method**: Congressional API + committee website crawling
- **Output**: Complete committee hierarchy with URLs and metadata
- **Validation**: Cross-reference with Senate.gov official committee list

#### Step 1.2: Hearing Discovery Engine (15 minutes)
- **Task**: Build comprehensive hearing discovery across all committees
- **Method**: Multi-source scraping (Congress.gov API + committee sites)
- **Output**: Master hearing database with metadata and processing status
- **Features**: ISVP detection, date filtering, duplicate detection

#### Step 1.3: Hearing Catalog Organization (5 minutes)
- **Task**: Organize discovered hearings for manual selection
- **Method**: Priority scoring based on recency, ISVP availability, duration
- **Output**: Sortable catalog with processing readiness assessment
- **Categories**: Ready, Needs Review, No Audio, Archived

### Phase 2: Manual Processing Framework (20 minutes)
**Objective**: Create manual controls for individual hearing processing

#### Step 2.1: Individual Hearing Controls (10 minutes)
- **Task**: Build manual processing triggers for each hearing
- **Method**: CLI commands and API endpoints for single-hearing processing
- **Output**: `process_hearing.py --hearing-id XXX --stage capture|transcribe|review`
- **Safety**: No bulk processing, confirmation prompts, rollback capability

#### Step 2.2: Processing Status Dashboard (10 minutes)
- **Task**: Real-time monitoring of individual hearing processing
- **Method**: Enhanced dashboard with per-hearing progress tracking
- **Output**: Visual progress indicators, logs, error handling
- **Features**: Start/stop controls, detailed logs, quality metrics

### Phase 3: Priority Hearing Selection (15 minutes)
**Objective**: Create curated test list for systematic validation

#### Step 3.1: Hearing Quality Assessment (10 minutes)
- **Task**: Automatically assess hearing processing feasibility
- **Method**: ISVP detection, duration analysis, audio quality prediction
- **Output**: Readiness scores and processing time estimates
- **Criteria**: ISVP availability, duration 20-120 minutes, recent date

#### Step 3.2: Test Priority Queue (5 minutes)
- **Task**: Generate recommended testing order
- **Method**: Committee diversity, audio quality, processing complexity
- **Output**: Prioritized list with rationale for each selection
- **Focus**: Different committees, various durations, different witness types

### Phase 4: Enhanced Testing Framework (25 minutes)
**Objective**: Systematic validation across multiple hearings

#### Step 4.1: Multi-Committee Validation (15 minutes)
- **Task**: Test processing pipeline across different committee types
- **Method**: Run existing validated pipeline on new hearings
- **Output**: Consistency metrics across committees
- **Analysis**: Processing time, accuracy, failure modes

#### Step 4.2: Feature Testing Suite (10 minutes)
- **Task**: Validate all existing features on new hearings
- **Method**: Run comprehensive test suite on each processed hearing
- **Output**: Feature compatibility matrix
- **Tests**: Audio quality, speaker ID, transcript enrichment, voice recognition

### Phase 5: System Integration (10 minutes)
**Objective**: Integrate discovery with existing processing pipeline

#### Step 5.1: Database Integration (5 minutes)
- **Task**: Connect discovery system to existing hearing database
- **Method**: Extend current schema with committee/subcommittee data
- **Output**: Unified hearing management system
- **Migration**: Preserve existing data, add new fields

#### Step 5.2: API Enhancement (5 minutes)
- **Task**: Extend APIs to support committee-based operations
- **Method**: Add committee filtering, bulk discovery, priority management
- **Output**: Enhanced API endpoints for committee-focused workflows
- **Endpoints**: `/committees`, `/hearings/by-committee`, `/hearings/priority`

## Detailed Implementation Steps

### STEP 1: Committee Structure Discovery
```bash
# Discover all Senate committees
python discover_committees.py --source congress_api --output data/committees/

# Validate committee structure
python validate_committee_structure.py --compare-official

# Generate committee hierarchy
python generate_committee_hierarchy.py --output data/committee_hierarchy.json
```

### STEP 2: Hearing Discovery Engine
```bash
# Discover hearings across all committees
python discover_hearings.py --committees all --date-range 2025-01-01:2025-12-31

# Assess hearing readiness
python assess_hearing_readiness.py --input data/discovered_hearings.json

# Generate priority recommendations
python generate_priority_list.py --output data/priority_hearings.json
```

### STEP 3: Manual Processing Framework
```bash
# Process individual hearing (manual trigger)
python process_hearing.py --hearing-id SSCI-2025-06-15 --stage capture --confirm

# Monitor processing status
python monitor_processing.py --hearing-id SSCI-2025-06-15 --follow

# Test specific features
python test_hearing_features.py --hearing-id SSCI-2025-06-15 --features audio,speaker,voice
```

### STEP 4: Enhanced Dashboard
```bash
# Start discovery dashboard
python run_discovery_dashboard.py --port 8002

# View at http://localhost:8002
# Features: Committee browser, hearing catalog, processing controls
```

## Expected Outcomes

### Discovery Results
- **Committee Coverage**: 20+ Senate committees and 40+ subcommittees
- **Hearing Catalog**: 200+ hearings from 2025 with processing assessment
- **Priority List**: 20-30 high-quality hearings for systematic testing
- **Readiness Assessment**: Processing time estimates and success probability

### Manual Processing Benefits
- **Controlled Testing**: Process one hearing at a time with full observation
- **Quality Validation**: Verify each step before moving to next hearing
- **Performance Analysis**: Detailed metrics per hearing for optimization
- **Risk Mitigation**: No bulk processing failures, manual intervention capability

### System Validation
- **Cross-Committee Consistency**: Validate pipeline works across all committee types
- **Feature Compatibility**: Ensure all existing features work with new hearings
- **Performance Benchmarks**: Establish processing time and accuracy baselines
- **Failure Mode Analysis**: Identify and address edge cases

## Risk Mitigation

### Technical Risks
- **Rate Limiting**: Implement delays and respect robots.txt
- **Audio Quality Variation**: Pre-assessment to avoid processing failures
- **Committee Website Changes**: Robust error handling and fallback methods
- **Processing Failures**: Rollback capability and detailed error logging

### Process Risks
- **Bulk Processing Temptation**: Strict manual controls with confirmation prompts
- **Quality Degradation**: Validate each hearing against existing benchmarks
- **Feature Regression**: Comprehensive testing suite for each new hearing
- **Data Corruption**: Backup systems and validation checks

## Success Metrics

### Discovery Metrics
- **Committee Coverage**: 100% of active Senate committees discovered
- **Hearing Availability**: 80%+ of recent hearings identified
- **ISVP Detection**: 90%+ accuracy in audio availability assessment
- **Processing Readiness**: 70%+ of identified hearings ready for processing

### Processing Metrics
- **Manual Control**: 100% of processing initiated manually
- **Success Rate**: 95%+ successful processing per hearing
- **Quality Consistency**: 90%+ accuracy maintained across committees
- **Performance**: Processing time within 2x of established benchmarks

### User Experience Metrics
- **Discovery Efficiency**: 50% improvement in hearing identification time
- **Processing Confidence**: Clear readiness assessment before processing
- **Monitoring Capability**: Real-time visibility into processing status
- **Control Granularity**: Ability to start/stop/rollback individual hearings

## Timeline

### Week 1: Discovery & Framework
- **Days 1-2**: Committee structure discovery and validation
- **Days 3-4**: Hearing discovery engine and catalog generation
- **Days 5-7**: Manual processing framework and dashboard enhancement

### Week 2: Testing & Validation
- **Days 1-3**: Process 10 high-priority hearings individually
- **Days 4-5**: Feature testing and cross-committee validation
- **Days 6-7**: Performance analysis and optimization

### Week 3: System Integration
- **Days 1-2**: Database integration and API enhancement
- **Days 3-5**: User interface refinement and documentation
- **Days 6-7**: Final testing and preparation for production deployment

## Next Steps After Completion

### Production Deployment Options
1. **Automated Batch Processing**: Enable bulk processing with manual approval
2. **Real-time Discovery**: Continuous monitoring for new hearings
3. **Advanced Analytics**: Cross-committee analysis and trending
4. **API Productization**: External access for researchers and organizations

### Feature Enhancements
1. **Live Hearing Processing**: Real-time transcription during hearings
2. **Advanced Speaker Diarization**: Multi-speaker conversation analysis
3. **Content Analysis**: Topic modeling and policy impact assessment
4. **Integration APIs**: Connect with external research and policy tools

## Approval Required

Please review this plan and confirm:
1. **Approach**: Multi-committee discovery with manual processing controls
2. **Timeline**: 3-week implementation with systematic validation
3. **Safety**: No bulk processing, individual hearing control, rollback capability
4. **Testing**: Comprehensive feature validation across multiple committees
5. **Integration**: Enhancement of existing systems without disruption

**Ready to proceed with Step 1.1: Committee Structure Discovery?**