# Step 3: Manual Pipeline Controls Implementation

## 🎯 **OBJECTIVE**
Add manual control buttons for each pipeline stage to the status page interface.

## 📋 **PIPELINE STAGES TO CONTROL**
1. **Discovered** → **Analyzed** (Analyze metadata and streams)
2. **Analyzed** → **Captured** (Capture audio)
3. **Captured** → **Transcribed** (Transcribe audio)
4. **Transcribed** → **Reviewed** (Review and assign speakers)
5. **Reviewed** → **Published** (Publish final results)

## 🔧 **IMPLEMENTATION PLAN**

### Phase 3A: Backend API Endpoints
- [ ] Add `/api/hearings/{id}/pipeline/analyze` endpoint
- [ ] Add `/api/hearings/{id}/pipeline/transcribe` endpoint  
- [ ] Add `/api/hearings/{id}/pipeline/review` endpoint
- [ ] Add `/api/hearings/{id}/pipeline/publish` endpoint
- [ ] Add `/api/hearings/{id}/pipeline/reset` endpoint (reset to previous stage)

### Phase 3B: Frontend Control Buttons
- [ ] Add action buttons to each pipeline stage section
- [ ] Add confirmation dialogs for each action
- [ ] Add progress indicators for active stages
- [ ] Add error handling and user feedback

### Phase 3C: Enhanced Status Display
- [ ] Add detailed stage information
- [ ] Add estimated processing times
- [ ] Add ability to view logs for each stage
- [ ] Add cancel/abort functionality

## 🎨 **ENHANCED STATUS PAGE LAYOUT**
```
Pipeline Stages:
┌─────────────────────────────────────────────────────────────┐
│ ✅ Discovered     [Complete]    [Restart] [View Details]    │
│ ⏳ Analyzed       [In Progress] [Cancel]  [View Details]    │
│ ⭕ Audio Captured [Start]       [Skip]    [View Details]    │
│ ⭕ Transcribed    [Start]       [Skip]    [View Details]    │
│ ⭕ Reviewed       [Start]       [Skip]    [View Details]    │
│ ⭕ Published      [Start]       [Skip]    [View Details]    │
└─────────────────────────────────────────────────────────────┘
```

## 📝 **PROGRESS LOG**
- [x] Phase 3A: Backend API endpoints
- [x] Phase 3B: Frontend control buttons
- [ ] Phase 3C: Enhanced status display
- [ ] Testing and validation

## ✅ **PHASE 3A COMPLETE: Backend API Endpoints**
Added pipeline control endpoints to simple_api_server.py:
- `/api/hearings/{id}/pipeline/analyze` - Manual analysis trigger
- `/api/hearings/{id}/pipeline/transcribe` - Manual transcription trigger  
- `/api/hearings/{id}/pipeline/review` - Manual review trigger
- `/api/hearings/{id}/pipeline/publish` - Manual publication trigger
- `/api/hearings/{id}/pipeline/reset` - Reset to specific stage

## ✅ **PHASE 3B COMPLETE: Frontend Control Buttons**
Created new PipelineControls component with:
- Manual action buttons for each pipeline stage
- Progress indicators and status badges
- Confirmation dialogs for destructive actions
- Reset functionality for each stage
- Global "Reset All Pipeline" control

## 🧪 **TESTING RESULTS**
Backend endpoints tested successfully:
- ✅ Analyze: hearing 47 (discovered → analyzed)
- ✅ Transcribe: hearing 37 (captured → transcribed)
- ✅ Reset: hearing 37 (transcribed → captured)

## 📝 **NEXT STEPS**
- [ ] Test frontend pipeline controls in browser
- [ ] Add enhanced status display features
- [ ] Add progress indicators and logging