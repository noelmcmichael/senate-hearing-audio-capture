# Real Data Recovery Plan - Senate Hearing Audio Capture System

## Current State Analysis

### What We Have
✅ **Production System**: https://senate-hearing-processor-1066017671167.us-central1.run.app  
✅ **React Frontend**: Enhanced UI with sophisticated filtering and search  
✅ **FastAPI Backend**: Comprehensive API with 45+ endpoints  
✅ **Database**: SQLite with auto-bootstrap system  
✅ **Processing Pipeline**: Complete audio → transcription → speaker ID workflow  
✅ **Infrastructure**: Cloud Run container with proper Docker setup  

### What's Missing
❌ **Real Hearing Data**: System only has bootstrap demo data  
❌ **Functional Capture Buttons**: Capture API exists but no real hearings to capture  
❌ **Working Audio Processing**: No actual audio streams being processed  
❌ **Speaker Identification**: No real transcripts with speaker labels  

### The Gap
The system was designed to process real Senate hearing audio, but we've been stuck in demo/bootstrap mode. We need to bridge back to the original goal: **automated discovery and processing of real Senate hearings with high-quality speaker-labeled transcripts**.

## Phase 1: Real Hearing Discovery (2 hours)

### Step 1.1: Activate Real Discovery Pipeline (30 minutes)
- **Objective**: Get real hearing data flowing into the system
- **Action**: Test and activate the Congress.gov API + committee scraping system
- **Expected Output**: 5-10 real hearings discovered from active Senate committees

```bash
# Test real hearing discovery
python discover_real_hearings.py --committees SCOM,SSCI,SSJU --limit 10

# Validate discovery results
python validate_discovered_hearings.py
```

### Step 1.2: Populate Production Database (30 minutes)
- **Objective**: Replace bootstrap data with real hearing records
- **Action**: Load discovered hearings into production database
- **Expected Output**: Production system showing real Senate hearings

```bash
# Clean bootstrap data and load real hearings
python populate_cloud_database.py --replace-bootstrap --real-hearings

# Verify database state
python check_current_system_state.py --production
```

### Step 1.3: Validate Frontend Display (30 minutes)
- **Objective**: Ensure real hearings display correctly in UI
- **Action**: Test frontend with real hearing data
- **Expected Output**: Dashboard showing real hearing titles, dates, and committees

### Step 1.4: Fix Capture Button Logic (30 minutes)
- **Objective**: Ensure capture buttons work with real hearings
- **Action**: Update capture logic to handle real hearing URLs
- **Expected Output**: Capture buttons that actually initiate audio processing

## Phase 2: Audio Capture Implementation (3 hours)

### Step 2.1: Test Audio Extraction (45 minutes)
- **Objective**: Verify audio extraction works on real hearings
- **Action**: Test ISVP and YouTube extraction on discovered hearings
- **Expected Output**: Working audio files from real Senate hearings

```bash
# Test audio extraction on real hearings
python test_real_audio_extraction.py --hearing-id [REAL_HEARING_ID]

# Verify audio quality
python verify_audio.py --file output/real_audio/[HEARING_ID].wav
```

### Step 2.2: Update Capture API (45 minutes)
- **Objective**: Fix capture API to handle real hearing URLs
- **Action**: Update capture endpoints to work with real hearing metadata
- **Expected Output**: Capture API that processes real Senate streaming URLs

### Step 2.3: Test End-to-End Capture (60 minutes)
- **Objective**: Verify complete capture workflow
- **Action**: Test capture button → audio extraction → file storage
- **Expected Output**: Complete audio files stored and linked to hearings

### Step 2.4: Integrate with Processing Pipeline (30 minutes)
- **Objective**: Connect capture to transcription pipeline
- **Action**: Ensure captured audio flows into Whisper transcription
- **Expected Output**: Automatic transcription after successful capture

## Phase 3: Transcription & Speaker ID (2 hours)

### Step 3.1: Test Whisper Integration (45 minutes)
- **Objective**: Verify transcription works on real captured audio
- **Action**: Test Whisper processing on real hearing audio
- **Expected Output**: High-quality transcripts from real Senate hearings

```bash
# Test transcription on real audio
python transcription_pipeline.py --audio output/real_audio/[HEARING_ID].wav --hearing-id [HEARING_ID]

# Verify transcript quality
python assess_transcript_quality.py --hearing-id [HEARING_ID]
```

### Step 3.2: Activate Speaker Identification (45 minutes)
- **Objective**: Get speaker labels working on real transcripts
- **Action**: Use congressional metadata to identify speakers
- **Expected Output**: Transcripts with CHAIR, MEMBER, WITNESS labels

### Step 3.3: Test Review Interface (30 minutes)
- **Objective**: Verify transcript review system works with real data
- **Action**: Test React review interface with real transcripts
- **Expected Output**: Functional speaker review and correction system

## Phase 4: Production Integration (1 hour)

### Step 4.1: Deploy Real Data System (30 minutes)
- **Objective**: Deploy updated system with real hearing capability
- **Action**: Update production container with real data processing
- **Expected Output**: Production system processing real Senate hearings

### Step 4.2: End-to-End Testing (30 minutes)
- **Objective**: Verify complete workflow in production
- **Action**: Test discover → display → capture → transcribe → review
- **Expected Output**: Complete working system with real hearing data

## Phase 5: Quality Assurance (1 hour)

### Step 5.1: Validate Audio Quality (20 minutes)
- **Objective**: Ensure captured audio meets quality standards
- **Action**: Test audio quality on multiple hearing types
- **Expected Output**: High-quality audio suitable for transcription

### Step 5.2: Validate Transcript Quality (20 minutes)
- **Objective**: Ensure transcripts meet accuracy standards
- **Action**: Test transcript quality on real congressional dialogue
- **Expected Output**: Accurate transcripts with proper speaker identification

### Step 5.3: Validate User Experience (20 minutes)
- **Objective**: Ensure UI works smoothly with real data
- **Action**: Test complete user workflow with real hearings
- **Expected Output**: Smooth user experience from discovery to transcript review

## Implementation Priority

### Critical Path (Must Fix First)
1. **Real Hearing Discovery** - Without real hearings, capture buttons are meaningless
2. **Audio Capture Logic** - Fix capture API to handle real hearing URLs
3. **Transcription Pipeline** - Ensure processing works on real audio
4. **Speaker Identification** - Get the core value proposition working

### Secondary Features (After Core Works)
- UI enhancements and polish
- Performance optimization
- Advanced filtering and search
- Bulk operations

## Success Metrics

### Phase 1 Success
- [ ] 5+ real hearings discovered and displayed
- [ ] Capture buttons appear for appropriate hearings
- [ ] Frontend displays real hearing titles and dates

### Phase 2 Success
- [ ] Audio extraction works on real hearing URLs
- [ ] Capture API successfully processes real hearings
- [ ] Audio files stored and linked to hearing records

### Phase 3 Success
- [ ] Transcription produces quality results on real audio
- [ ] Speaker identification labels real congressional speakers
- [ ] Review interface works with real transcript data

### Phase 4 Success
- [ ] Production system processes real hearings end-to-end
- [ ] Complete workflow: discover → capture → transcribe → review
- [ ] High-quality speaker-labeled transcripts produced

## Risk Mitigation

### Technical Risks
- **Real hearings may not be available**: Focus on recent hearings with known audio
- **Audio quality issues**: Test multiple hearing types and sources
- **Transcription accuracy**: Validate against known transcripts where possible

### Timeline Risks
- **Phase dependencies**: Each phase depends on previous success
- **Real data complexity**: Real hearings more complex than bootstrap data
- **Production deployment**: Cloud deployment may have unique issues

## Next Steps

1. **Immediate**: Start with Phase 1 - Real Hearing Discovery
2. **Document Progress**: Update README.md after each successful phase
3. **Commit Early**: Commit working code after each successful step
4. **Test Thoroughly**: Validate each phase before moving to next

The goal is to get back to our original vision: **automated discovery and processing of real Senate hearings with high-quality speaker-labeled transcripts**.