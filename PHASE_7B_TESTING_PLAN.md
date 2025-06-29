# Phase 7B Enhanced UI - Functional Testing Plan

## 🎯 **Testing Objective**
Validate Phase 7B enhanced UI functionality, identify bugs, and ensure system works as described before considering production hardening.

## 📋 **Pre-Testing Setup**

### **Step 1: Environment Check**
```bash
# Check current project state
cd /Users/noelmcmichael/Workspace/senate_hearing_audio_capture
ls -la

# Check if demo data exists
python -c "
from src.api.database_enhanced import get_enhanced_db
db = get_enhanced_db()
cursor = db.execute('SELECT COUNT(*) FROM hearings')
print(f'Hearings in database: {cursor.fetchone()[0]}')
db.close()
"
```

### **Step 2: Demo Data Setup** 
```bash
# Run the Phase 7B demo setup (if needed)
python demo_phase7b_enhanced_ui.py
```

### **Step 3: System Startup**
```bash
# Terminal 1: Start FastAPI backend
python -m uvicorn src.api.main_app:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2: Start React frontend  
cd dashboard && npm start

# Should open http://localhost:3000 automatically
```

---

## 🧪 **Test Cases**

### **Test 1: Basic System Startup**
**Objective**: Verify both backend and frontend start without errors

**Steps**:
1. Start FastAPI backend - should show startup logs
2. Start React frontend - should compile and open browser
3. Check API docs at http://localhost:8001/api/docs
4. Check main dashboard at http://localhost:3000

**Expected Result**:
- No startup errors in either terminal
- API docs page loads with all endpoints
- Dashboard loads with navigation elements

**Pass/Fail**: ___________

---

### **Test 2: Database Integration**
**Objective**: Verify enhanced database has demo data

**Steps**:
```bash
# Check database tables exist
python -c "
from src.api.database_enhanced import get_enhanced_db
db = get_enhanced_db()
tables = db.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall()
print('Tables:', [t[0] for t in tables])
db.close()
"

# Check sample data counts
python -c "
from src.api.database_enhanced import get_enhanced_db
db = get_enhanced_db()
print('Hearings:', db.execute('SELECT COUNT(*) FROM hearings').fetchone()[0])
print('User sessions:', db.execute('SELECT COUNT(*) FROM user_sessions').fetchone()[0])
print('System alerts:', db.execute('SELECT COUNT(*) FROM system_alerts').fetchone()[0])
db.close()
"
```

**Expected Result**:
- All Phase 7B tables exist (hearings, user_sessions, system_alerts, etc.)
- Demo data present (5+ hearings, 4+ user sessions, 3+ alerts)

**Pass/Fail**: ___________

---

### **Test 3: API Endpoints**
**Objective**: Verify all Phase 7B APIs respond correctly

**Steps**:
```bash
# Test hearing management APIs
curl "http://localhost:8001/api/hearings/queue" | python -m json.tool
curl "http://localhost:8001/api/hearings/committees" | python -m json.tool

# Test system monitoring APIs  
curl "http://localhost:8001/api/monitoring/health" | python -m json.tool
curl "http://localhost:8001/api/monitoring/alerts" | python -m json.tool

# Test legacy dashboard APIs
curl "http://localhost:8001/api/dashboard/hearings" | python -m json.tool
```

**Expected Result**:
- All endpoints return valid JSON responses
- Hearing queue shows 5+ hearings with filtering options
- Health check shows system status
- Alerts show 3+ test alerts

**Pass/Fail**: ___________

---

### **Test 4: React Dashboard UI**
**Objective**: Verify all UI components render and function

**Manual Testing Steps**:
1. **Main Dashboard** (http://localhost:3000):
   - [ ] Page loads without console errors
   - [ ] Navigation menu is visible
   - [ ] Hearing list displays with data
   - [ ] Statistics cards show counts

2. **Hearing Queue** (navigate to Hearing Queue):
   - [ ] Hearing list displays with filtering options
   - [ ] Filter by committee works
   - [ ] Filter by status works  
   - [ ] Priority indicators visible
   - [ ] Capture buttons present

3. **System Health** (navigate to System Health):
   - [ ] Health status indicators display
   - [ ] Alert list shows current alerts
   - [ ] Performance metrics visible
   - [ ] Component status shows

4. **Navigation**:
   - [ ] All navigation links work
   - [ ] Page transitions smooth
   - [ ] Browser back/forward works

**Pass/Fail**: ___________

---

### **Test 5: Hearing Management Features**
**Objective**: Test hearing queue filtering and management

**Steps**:
1. Open Hearing Queue interface
2. Test committee filter dropdown - select different committee
3. Test status filter - try different status values
4. Test search functionality (if present)
5. Click on hearing details to view more info
6. Test capture trigger button (should show confirmation)

**Expected Result**:
- Filters work and update hearing list
- Hearing details display correctly
- Interactive elements respond appropriately

**Pass/Fail**: ___________

---

### **Test 6: System Monitoring Features**
**Objective**: Test real-time monitoring displays

**Steps**:
1. Open System Health interface
2. Check if health indicators are color-coded
3. View alert details by clicking on alerts
4. Check if sync status shows component health
5. Look for performance metrics/charts

**Expected Result**:
- Health status displays clearly with visual indicators
- Alert details are accessible
- Monitoring data appears accurate

**Pass/Fail**: ___________

---

### **Test 7: Real-time Updates (WebSocket)**
**Objective**: Verify WebSocket real-time functionality

**Steps**:
1. Open two browser tabs to the dashboard
2. Check browser developer console for WebSocket connection
3. Monitor for real-time updates in UI
4. Check if status changes propagate between tabs

**Note**: This may be limited in demo environment

**Expected Result**:
- WebSocket connection established (check Network tab)
- No WebSocket errors in console

**Pass/Fail**: ___________

---

### **Test 8: Error Handling**
**Objective**: Verify graceful error handling

**Steps**:
1. Stop the FastAPI backend while frontend is running
2. Check if frontend shows connection error gracefully
3. Restart backend and see if frontend recovers
4. Try accessing invalid API endpoints manually

**Expected Result**:
- Frontend handles backend disconnection gracefully
- Error messages are user-friendly
- System recovers when backend restarts

**Pass/Fail**: ___________

---

### **Test 9: Performance & Responsiveness**
**Objective**: Check basic performance characteristics

**Steps**:
1. Check page load times (should be reasonable)
2. Test responsive design by resizing browser window
3. Navigate between different sections multiple times
4. Check browser developer tools for console errors

**Expected Result**:
- Pages load within reasonable time (<5 seconds)
- UI adapts to different screen sizes
- No JavaScript errors in console

**Pass/Fail**: ___________

---

### **Test 10: Data Integration**
**Objective**: Verify Phase 7A data integration works

**Steps**:
1. Check if hearing data includes congressional metadata
2. Verify committee information displays correctly
3. Check if sync status reflects actual data sources
4. Validate data consistency across different views

**Expected Result**:
- Congressional metadata present in hearing records
- Committee information accurate
- Data consistent across UI components

**Pass/Fail**: ___________

---

## 🐛 **Bug Tracking Template**

For each bug found, document:

### **Bug #__: [Title]**
- **Component**: [Which part of system]
- **Severity**: [Critical/High/Medium/Low]
- **Steps to Reproduce**:
  1. 
  2. 
  3. 
- **Expected Behavior**: 
- **Actual Behavior**: 
- **Error Messages**: 
- **Screenshot/Logs**: 

---

## 📊 **Test Results Summary**

### **Test Execution Date**: ___________
### **Tester**: ___________

**Results**:
- **Tests Passed**: ___/10
- **Tests Failed**: ___/10
- **Bugs Found**: ___
- **Critical Issues**: ___

### **Overall Assessment**:
- [ ] **Ready for basic use** - minor bugs only
- [ ] **Needs bug fixes** - several issues to address
- [ ] **Major issues** - significant problems found
- [ ] **Not functional** - system doesn't work as described

### **Priority Bug Fixes Needed**:
1. 
2. 
3. 

### **Nice-to-Have Improvements**:
1. 
2. 
3. 

---

## 🚀 **Next Steps After Testing**

Based on test results:

### **If Tests Pass (8+/10)**:
- Document any minor bugs found
- Consider Phase 7B functionally complete
- Proceed with confidence to next enhancement phase

### **If Mixed Results (5-7/10)**:
- Fix critical and high-priority bugs
- Re-test problem areas
- Improve error handling and user experience

### **If Poor Results (<5/10)**:
- Focus on core functionality fixes
- Simplify complex features that aren't working
- Consider stepping back to Phase 7A for stability

---

*This testing plan focuses on functional validation rather than security or production readiness. The goal is to ensure the enhanced UI works as described before adding complexity.*