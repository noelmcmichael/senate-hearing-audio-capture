# Data Quality Investigation & Fix Plan

## Issues Discovered

### 1. Status Field Confusion
**Problem**: All hearings show `status: "complete"` and `processing_stage: "published"` regardless of actual state
**Root Cause**: Demo script hardcodes all hearings as completed in the creation process
**Impact**: User cannot distinguish between hearings at different stages

### 2. Poor Transcript Quality
**Problem**: Only 3 segments per transcript instead of full hearing content
**Root Cause**: Mock transcript generation creates minimal test data
**Files Affected**: All `hearing_*_transcript.json` files (17 total)

### 3. Status Field Meanings Unclear
**Current State**: 
- `status: "complete"` 
- `processing_stage: "published"`
**Questions**: What should these actually represent in the hearing lifecycle?

### 4. Real vs Test Data Mixed
**Real Audio Found**: `senate_hearing_20250627_123720_stream1_complete_transcript.json` 
- 140+ segments from actual Whisper transcription
- Poor quality audio (repeated "thank you" phrases)
- Shows what real data structure should look like

## Proposed Status Definitions

### Processing Pipeline Stages
1. **discovered** - Hearing found in Congress API or committee website
2. **scheduled** - Date/time confirmed, ready for capture
3. **capturing** - Audio capture in progress
4. **captured** - Audio file saved and verified
5. **transcribing** - Whisper processing in progress  
6. **transcribed** - Raw transcript available
7. **reviewing** - Human speaker identification in progress
8. **reviewed** - Speaker assignment complete
9. **published** - Final transcript ready for use

### Overall Status Categories
- **in_progress** - Any stage before "published"
- **complete** - Published and ready
- **error** - Failed at some stage
- **needs_review** - Requires human attention

## Fix Implementation Plan

### Step 1: Update Database Schema
- Add clear status and stage definitions
- Create realistic demo data with varied statuses
- Include proper progression timestamps

### Step 2: Create Quality Transcript Samples
- Generate 5-10 realistic hearing transcripts
- 50-200 segments per hearing
- Proper speaker roles (CHAIR, RANKING, MEMBER, WITNESS)
- Meaningful content instead of "thank you" repetition

### Step 3: Update API Server
- Serve actual status information
- Return hearing titles properly
- Handle transcript availability correctly

### Step 4: Fix Frontend Display
- Show meaningful status badges
- Display actual progress indicators
- Handle various hearing states properly

## Expected Outcomes

1. **Clear Status Progression**: Users see hearings at various realistic stages
2. **Quality Transcripts**: Meaningful content for speaker identification workflow
3. **Proper Data Flow**: API serves real information instead of placeholder data
4. **User Understanding**: Clear meaning of "published" vs other statuses

## Time Estimate: 2-3 hours
- 1 hour: Database schema and data cleanup
- 1 hour: Quality transcript generation
- 30 min: API and frontend updates
- 30 min: Testing and verification