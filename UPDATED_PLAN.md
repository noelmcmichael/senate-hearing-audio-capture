# Updated Senate Hearing Audio Capture Plan
## Selective Automation Strategy

### Current Status (From Previous Session)
- ✅ Cloud infrastructure deployed and validated  
- ✅ Core services working (health, storage, transcription)
- ✅ Real hearing discovery working
- ✅ ISVP player detection working
- 🔄 15% remaining: Browser dependencies for capture service

### User Requirements & Clarifications
1. **Browser Support**: Chrome only (not concerned with other browsers)
2. **NO End-to-End Automation**: Don't automatically process everything discovered
3. **Selective Processing**: Manual trigger per hearing with "capture hearing" button
4. **Discovery Automation**: Yes, automatically discover hearings that meet requirements
5. **Post-Capture Automation**: Once triggered, automate full pipeline (capture → convert → trim → transcribe → speaker labels)

---

## REVISED MILESTONE PLAN

### **Milestone 4: Discovery Dashboard & Selective Processing (60 minutes)**

#### **Step 4.1: Discovery Dashboard Backend (20 minutes)**
- **API Endpoint**: `GET /api/hearings/discover` - Returns list of discovered hearings
- **API Endpoint**: `POST /api/hearings/{id}/capture` - Triggers processing pipeline for selected hearing
- **Database Schema**: Store discovered hearings with metadata
- **Hearing Status**: Track status (discovered, processing, completed, failed)

#### **Step 4.2: Discovery Dashboard Frontend (25 minutes)**
- **Hearings List View**: Display discovered hearings with descriptions
- **Hearing Cards**: Show title, date, committee, summary, media indicators
- **Capture Button**: "Capture Hearing" button per hearing
- **Status Indicators**: Visual status (waiting, processing, completed)
- **Refresh Discovery**: Button to run new discovery

#### **Step 4.3: Processing Pipeline Integration (15 minutes)**
- **Pipeline Controller**: Orchestrate capture → convert → trim → transcribe
- **Progress Tracking**: Real-time status updates
- **Error Handling**: Graceful failure handling per step
- **Notification System**: Success/failure alerts

### **Milestone 5: Chrome/Docker Fix & Production Optimization (30 minutes)**

#### **Step 5.1: Chrome Browser Dependencies (15 minutes)**
- **Dockerfile Update**: Add Chrome-specific dependencies
- **Playwright Chrome**: Install only Chrome browser
- **Container Optimization**: Minimal Chrome installation
- **Testing**: Verify capture service works in cloud

#### **Step 5.2: Production Optimization (15 minutes)**
- **Audio Trimming**: Implement silence removal from start of hearings
- **Speaker Labeling**: Enhance transcription with speaker identification
- **Error Recovery**: Robust error handling and retry logic
- **Performance Monitoring**: Add basic metrics and logging

---

## TECHNICAL ARCHITECTURE

### **New Components Needed**

#### **Backend Services**
```
src/api/discovery_service.py     # Automated hearing discovery
src/api/pipeline_controller.py   # Orchestrate processing pipeline
src/api/hearing_manager.py       # Manage hearing lifecycle
src/models/hearing.py            # Database model for hearings
```

#### **Frontend Components**
```
src/components/DiscoveryDashboard.tsx   # Main dashboard view
src/components/HearingCard.tsx          # Individual hearing display
src/components/ProcessingStatus.tsx     # Status indicator component
src/hooks/useHearingDiscovery.ts        # Discovery API hook
src/hooks/useHearingCapture.ts          # Capture trigger hook
```

#### **Database Schema**
```sql
CREATE TABLE discovered_hearings (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    url VARCHAR(500) NOT NULL,
    committee VARCHAR(200),
    date_scheduled TIMESTAMP,
    description TEXT,
    media_indicators JSONB,
    status VARCHAR(50) DEFAULT 'discovered',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### **Processing Pipeline States**
1. **discovered** - Found during discovery, waiting for manual trigger
2. **capture_requested** - User clicked "Capture Hearing" button
3. **capturing** - Downloading audio from ISVP player
4. **converting** - Converting to MP3 format
5. **trimming** - Removing silence from beginning
6. **transcribing** - Converting audio to text
7. **labeling** - Adding speaker identification
8. **completed** - Full processing finished
9. **failed** - Error occurred, needs review

### **User Workflow**
1. **Auto-Discovery**: System runs periodic discovery of new hearings
2. **Review Dashboard**: User sees list of discovered hearings
3. **Manual Selection**: User clicks "Capture Hearing" on desired hearings
4. **Automated Processing**: System handles full pipeline once triggered
5. **Status Monitoring**: User can monitor progress in real-time

---

## EXECUTION PLAN

### **Phase 1: Backend Foundation (25 minutes)**
- Set up discovery service and database schema
- Create pipeline controller for orchestrating processing
- Add API endpoints for discovery and capture triggering

### **Phase 2: Frontend Dashboard (25 minutes)**
- Build discovery dashboard with hearing cards
- Add capture buttons and status indicators
- Implement real-time status updates

### **Phase 3: Chrome Fix & Optimization (20 minutes)**
- Resolve Chrome browser dependencies in Docker
- Add audio trimming and speaker labeling
- Test end-to-end pipeline

### **Phase 4: Integration Testing (20 minutes)**
- Test full discovery → manual trigger → processing pipeline
- Validate with real Senate hearings
- Ensure robust error handling

---

## SUCCESS CRITERIA

### **Milestone 4 Success**
- ✅ Discovery runs automatically and finds hearings
- ✅ Dashboard shows discovered hearings with "Capture" buttons
- ✅ Manual trigger initiates full processing pipeline
- ✅ Real-time status updates work correctly

### **Milestone 5 Success**
- ✅ Chrome browser works in Docker container
- ✅ Audio trimming removes silence from hearing start
- ✅ Speaker labeling identifies different speakers
- ✅ Full pipeline completes end-to-end successfully

### **Overall Success**
- ✅ User can review discovered hearings before processing
- ✅ System processes only selected hearings
- ✅ Full automation after manual trigger
- ✅ Production-ready, selective processing platform

---

## NEXT STEPS

This plan gives you **complete control** over which hearings to process while **automating the discovery** and **full processing pipeline** once triggered. You can test one hearing at a time, choose important hearings, and avoid overwhelming the system.

**Ready to proceed with Milestone 4: Discovery Dashboard & Selective Processing?**