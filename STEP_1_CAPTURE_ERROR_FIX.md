# Step 1: Fix 500 Error on Capture Button

## 🔍 **ERROR ANALYSIS**
- **Error**: 500 Internal Server Error
- **Endpoint**: `/api/hearings/44/capture?user_id=demo-user-001`
- **Frontend Error**: "Failed to start capture: Unknown error"

## 🛠 **INVESTIGATION PLAN**
1. Check server logs for detailed error
2. Examine current capture endpoint implementation
3. Test endpoint directly with curl
4. Fix implementation and test

## 📋 **PROGRESS LOG**
- [x] Check server logs
- [x] Examine capture endpoint code
- [x] Test endpoint directly
- [x] Fix implementation
- [x] Validate fix works

## 🔧 **ROOT CAUSE IDENTIFIED**
The capture endpoint was trying to set `processing_stage = 'capturing'`, but the database CHECK constraint only allows: `('discovered', 'analyzed', 'captured', 'transcribed', 'reviewed', 'published')`.

## ✅ **FIX APPLIED**
Changed `processing_stage = 'capturing'` to `processing_stage = 'captured'` in the capture endpoint.

## 🧪 **TESTING RESULTS**
- Hearing ID 44: ✅ Success - "Audio capture initiated for hearing: Bootstrap Entry for Senate Committee on the Judiciary"
- Hearing ID 37: ✅ Success - "Audio capture initiated for hearing: Executive Business Meeting"

## 📝 **NEXT STEPS**
Ready to proceed to Step 2: Remove automatic processing and implement manual controls.