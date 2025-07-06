# Phase 3.3: Production Control System Implementation Plan

## 🎯 **OBJECTIVE**
Transform the current system from automatic processing to full manual control with user-initiated pipeline stages.

## 🚨 **CRITICAL ISSUES IDENTIFIED**

### 1. **500 Error on Capture Button**
- **Error**: `Failed to load resource: the server responded with a status of 500 (INTERNAL SERVER ERROR)`
- **Location**: `/api/hearings/44/capture?user_id=demo-user-001`
- **Root Cause**: TBD - need to investigate capture endpoint implementation

### 2. **Automatic Processing Happening**
- **Issue**: Hearings showing "Published", "Audio Captured", "Transcribed" without user intervention
- **Risk**: Uncontrolled resource usage and processing in production
- **Requirement**: All pipeline stages must require explicit user action

### 3. **Pipeline Control Gaps**
- **Current**: Shows completed stages but no way to control them
- **Needed**: Manual trigger buttons for each pipeline stage
- **Missing**: Restart/reset functionality for failed or unwanted captures

## 📋 **ENHANCEMENT PLAN**

### **Step 1: Fix 500 Error on Capture Button**
- [ ] Investigate current capture endpoint implementation
- [ ] Debug the specific error for hearing ID 44
- [ ] Test capture functionality with proper error handling
- [ ] Ensure capture endpoint returns meaningful error messages

### **Step 2: Implement Manual Pipeline Controls**
- [ ] Add action buttons for each pipeline stage:
  - **Discover**: Manual hearing discovery (if not auto-discovered)
  - **Analyze**: Manual metadata and stream analysis
  - **Capture**: Manual audio capture initiation
  - **Transcribe**: Manual transcription processing
  - **Review**: Manual quality review and speaker identification
  - **Publish**: Manual final publication
- [ ] Add confirmation dialogs for each action
- [ ] Implement progress indicators for active stages
- [ ] Add cancel/abort functionality for running processes

### **Step 3: Restart/Reset Functionality**
- [ ] Add "Restart" button for each completed stage
- [ ] Implement "Reset All" functionality to clear all progress
- [ ] Add confirmation prompts for destructive actions
- [ ] Preserve original data when restarting stages

### **Step 4: Enhanced Status Page Features**
- [ ] Add estimated time remaining for active processes
- [ ] Show detailed logs for each pipeline stage
- [ ] Add ability to download artifacts (audio files, transcripts)
- [ ] Implement real-time progress updates via websockets
- [ ] Add troubleshooting information for failed stages

### **Step 5: Production Safety Controls**
- [ ] Remove all automatic processing triggers
- [ ] Implement user authentication for sensitive actions
- [ ] Add resource usage monitoring and limits
- [ ] Implement audit logging for all user actions
- [ ] Add batch processing controls for multiple hearings

## 🔧 **TECHNICAL IMPLEMENTATION**

### **Enhanced Status Page Layout**
```
┌─────────────────────────────────────────────────────────────┐
│ Hearing Title                                    [Settings] │
│ Committee • Date • Status                                    │
├─────────────────────────────────────────────────────────────┤
│ Processing Status: [Progress Bar]                [Refresh]   │
├─────────────────────────────────────────────────────────────┤
│ Pipeline Stages:                                             │
│                                                             │
│ ○ Discovered     [✓] Complete    [Restart] [View Details]   │
│ ○ Analyzed       [✓] Complete    [Restart] [View Details]   │
│ ○ Audio Captured [⚠] In Progress [Cancel]  [View Details]   │
│ ○ Transcribed    [○] Pending     [Start]   [View Details]   │
│ ○ Reviewed       [○] Pending     [Start]   [View Details]   │
│ ○ Published      [○] Pending     [Start]   [View Details]   │
│                                                             │
│ [Reset All Pipeline] [Download All Artifacts]               │
├─────────────────────────────────────────────────────────────┤
│ Technical Details:                                           │
│ • Audio Quality: 44.1kHz, 16-bit                           │
│ • Transcript Segments: 247                                   │
│ • Processing Time: 12m 34s                                   │
│ • Storage Used: 125.3 MB                                     │
├─────────────────────────────────────────────────────────────┤
│ Recent Activity:                                             │
│ • 2:34 PM - Audio capture started                           │
│ • 2:31 PM - Stream analysis completed                       │
│ • 2:29 PM - Hearing discovered                              │
└─────────────────────────────────────────────────────────────┘
```

### **API Endpoints to Implement**
- `POST /api/hearings/{id}/pipeline/discover` - Manual discovery
- `POST /api/hearings/{id}/pipeline/analyze` - Manual analysis
- `POST /api/hearings/{id}/pipeline/capture` - Manual capture (fix existing)
- `POST /api/hearings/{id}/pipeline/transcribe` - Manual transcription
- `POST /api/hearings/{id}/pipeline/review` - Manual review
- `POST /api/hearings/{id}/pipeline/publish` - Manual publication
- `POST /api/hearings/{id}/pipeline/reset` - Reset specific stage
- `POST /api/hearings/{id}/pipeline/reset-all` - Reset all stages
- `DELETE /api/hearings/{id}/pipeline/{stage}` - Cancel active stage

### **Database Schema Updates**
- Add `pipeline_stage_logs` table for detailed logging
- Add `user_actions` table for audit trail
- Add `processing_locks` table to prevent concurrent operations
- Update `hearings_unified` with more granular status fields

## 🎯 **SUCCESS CRITERIA**

### **Immediate (Phase 3.3)**
- [ ] Capture button 500 error fixed
- [ ] Manual controls for all pipeline stages
- [ ] No automatic processing in production
- [ ] Restart/reset functionality working

### **Enhanced (Phase 3.4)**
- [ ] Real-time progress updates
- [ ] Detailed logging and audit trails
- [ ] Resource usage monitoring
- [ ] Batch processing controls

## 📅 **IMPLEMENTATION ORDER**

1. **Critical Fix**: Resolve 500 error on capture button
2. **Safety First**: Remove all automatic processing
3. **Core Controls**: Implement manual pipeline stage controls
4. **Reset Functionality**: Add restart/reset capabilities
5. **Enhanced UX**: Add progress indicators and detailed logging
6. **Production Safety**: Add authentication and resource limits

## 🤔 **DISCUSSION POINTS**

1. **Authentication**: Should pipeline controls require user login?
2. **Resource Limits**: What limits should we set for concurrent processing?
3. **Data Retention**: How long should we keep processing logs and artifacts?
4. **Notification System**: Should we add email/SMS alerts for completed stages?
5. **Batch Operations**: Should we allow bulk operations on multiple hearings?

---

**Next Steps**: 
1. Investigate and fix the 500 error
2. Implement manual controls for pipeline stages
3. Add restart/reset functionality
4. Enhance status page with detailed controls