# Senate Hearing Audio Capture - Step-by-Step Plan

**Date**: 2025-01-02  
**Goal**: Get to milestone of seeing discovered hearings and manually testing one  
**Estimated Time**: 30 minutes  

## 📊 Current State Analysis

### ✅ Infrastructure Ready (75%)
- **Cloud Run Service**: ✅ Operational at https://senate-hearing-processor-518203250893.us-central1.run.app
- **Database**: ✅ Healthy PostgreSQL connection (0.338s response time)
- **API Endpoints**: ✅ 45+ endpoints available and responding
- **Storage**: ✅ GCS permissions fixed (major blocker resolved)

### ❌ Critical Blocker: Empty Database
- **Problem**: No committees or hearings in database
- **Impact**: Discovery endpoints return empty results
- **Solution**: Import minimal test data (3 committees + 3 hearings)

### ⚠️ Minor Issues (Non-blocking)
- **Congress API**: Key authentication issue (workaround available)
- **Redis**: Disabled (system works without it)

## 🚀 Implementation Plan

### **Step 1: Database Population (10 minutes)**
**Objective**: Import minimal test data to enable discovery

**Actions:**
1. ✅ Review test data structure (3 committees + 3 hearings - appropriate size)
2. Use Cloud Shell to import test_data.sql directly
3. Verify database tables populated correctly
4. Test API endpoints return data

**Expected Results:**
- Committees table: 3 rows (SCOM, SSCI, SSJU)
- Hearings table: 3 rows (recent test hearings)
- API responses: `/api/committees` and `/api/stats` return data

### **Step 2: API Validation (10 minutes)**  
**Objective**: Verify all critical endpoints work with populated data

**Actions:**
1. Test `/api/committees` - should return 3 committees
2. Test `/api/stats` - should return statistics
3. Test `/api/hearings/discover` - should return 3 hearings
4. Test `/api/hearings/{id}` - should return hearing details

**Expected Results:**
- All API endpoints respond with valid data
- No NoneType errors or empty responses
- Hearing discovery returns processable hearings

### **Step 3: Manual Processing Test (10 minutes)**
**Objective**: Test manual hearing capture and processing

**Actions:**
1. Pick one hearing from discovery results
2. Test manual capture process (may simulate if needed)
3. Verify basic processing pipeline initiation
4. Confirm user can trigger hearing processing

**Expected Results:**
- User can see list of discovered hearings
- Can trigger processing of selected hearing
- Processing pipeline initiates (even if simulated)

## 🎯 Success Criteria

### **Milestone Achievement:**
- ✅ User can see discovered hearings list
- ✅ User can manually trigger hearing processing
- ✅ System responds to processing requests
- ✅ Basic end-to-end workflow functional

### **API Endpoints Working:**
- `GET /api/committees` → 3 committees
- `GET /api/stats` → valid statistics
- `POST /api/hearings/discover` → 3 hearings
- `GET /api/hearings/{id}` → hearing details

### **User Experience:**
- Dashboard shows discovered hearings
- "Capture Audio" buttons functional
- Processing status updates
- Clear feedback on actions

## 🔧 Implementation Notes

### **Database Strategy:**
- Use minimal test data (not legacy bulk data)
- Focus on functional verification, not comprehensive data
- Keep import small and fast for testing

### **Testing Approach:**
- Test each API endpoint individually
- Verify data flow through system
- Focus on user-visible functionality

### **Commit Strategy:**
- Commit after each successful step
- Document progress in README.md
- Track time spent on each step

## 📋 Next Steps After Milestone

Once basic discovery is working:
1. **Congress API Fix**: Resolve authentication issue
2. **Real Discovery**: Connect to live hearing data
3. **Enhanced Processing**: Full audio capture pipeline
4. **Production Optimization**: Scale and optimize

---

**Started**: 2025-01-02  
**Target Completion**: 30 minutes  
**Documentation**: Track progress in README.md  