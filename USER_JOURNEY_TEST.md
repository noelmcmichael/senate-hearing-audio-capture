# 🎯 User Journey Test: Working Functionality Demo

## **Test the Core User Journey**

### **Prerequisites**
- Backend running on http://localhost:8001 ✅
- Frontend running on http://localhost:3000 ✅
- Background processor active ✅

### **Test Path 1: Browse → Details → Capture**

1. **Start**: Go to http://localhost:3000
2. **Navigate**: Click "Hearing Queue" button (blue button in top right)
3. **Browse**: See list of hearings with pipeline status indicators
4. **View Details**: Click "Details" button on any hearing
5. **Modal Check**: Modal should appear **immediately** (no navigation needed)
6. **Review Info**: See comprehensive hearing information and pipeline status
7. **Test Capture**: 
   - If hearing not published: Click "Capture Audio" → See loading state → Success message
   - If hearing published: See "Already Published" status
8. **View Transcript**: If available, click "View Transcript" → Navigate to transcript browser

### **Test Path 2: Committee Browser → Details**

1. **Navigate**: Click "Committees" button (purple button)
2. **Select Committee**: Click on any committee (e.g., "SCOM")
3. **Browse Hearings**: See committee-specific hearings
4. **View Details**: Click "View Details" on any hearing
5. **Test**: Same modal and capture functionality as above

### **Expected Results**

#### **✅ Modal Display**
- Modal appears immediately when clicking "Details"
- No need to navigate away to see it
- High z-index (9999) ensures it's on top

#### **✅ Capture Functionality**
- Button shows "Capture Audio" for non-published hearings
- Clicking shows "Capturing..." loading state
- Success shows green checkmark with message
- Error shows red error message
- Published hearings show "Already Published"

#### **✅ Pipeline Status**
- Real-time status indicators (polling every 5 seconds)
- Accurate stage progression: discovered → analyzed → captured → transcribed → reviewed → published
- Visual progress bar with stage icons
- Processing animations when status is "processing"

#### **✅ Integration Points**
- Hearing details connect to real API data
- Capture connects to real backend endpoint
- Transcript links navigate to transcript browser
- Background processor actively advancing hearings

### **Known Working API Endpoints** (from integration test)
- ✅ `GET /api` - API health
- ✅ `GET /api/committees` - Committee list
- ✅ `GET /api/committees/{code}/hearings` - Committee hearings
- ✅ `GET /api/hearings/{id}` - Hearing details
- ✅ `POST /api/hearings/{id}/capture` - Trigger capture

### **Console Verification**
Check browser console for:
- No React warnings about JSX attributes
- Successful API calls to localhost:8001
- Capture success/error responses
- Real-time status updates

### **Pipeline Progression Test**
Monitor `logs/simple_processor.log` to see:
```
Processing hearings through stages...
✅ Hearing → next_stage
```

## **Success Criteria**
- [ ] Modal appears immediately on click
- [ ] Capture button provides immediate feedback
- [ ] Pipeline status accurately reflects hearing state
- [ ] No browser alerts (all feedback in UI)
- [ ] Transcript integration works
- [ ] Console shows clean API responses
- [ ] Background processor advancing hearings

## **If Issues Found**
1. Check logs: `tail -20 logs/simple_processor.log` and `logs/api_server.log`
2. Verify services: Backend (8001) and Frontend (3000) running
3. Check browser console for errors
4. Test individual API endpoints with integration test script

The core functionality is now working end-to-end!