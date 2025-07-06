# Functional Fixes Plan: UI Issues

## Problems Identified from User Feedback

### 1. **Capture Audio Button Error (422)**
- Console error: `/api/hearings/1/capture:1 Failed to load resource: the server responded with a status of 422 ()`
- Button gives error when clicked
- Need to fix capture endpoint or provide better error handling

### 2. **Misleading Status Indicators**
- "View Transcript" button shows but no transcript exists
- "Processing" status shows but no capture was actually started
- Status variety is artificial/fake rather than reflecting actual system state

### 3. **Incorrect Dates**
- Cards show bootstrap creation dates (2025-07-06) instead of realistic hearing dates
- Should show actual hearing dates, not discovery dates

### 4. **Missing Transcript Data**
- "View Transcript" link goes to page but no transcript exists
- Either need to create sample transcript data or hide the button

## Solution Steps

### Step 1: Fix Hearing Dates (5 min)
- Update bootstrap data to use realistic hearing dates in the past
- Ensure dates reflect actual hearing times, not system creation times

### Step 2: Fix Status Logic (10 min)
- Remove artificial status variety based on ID
- Make status indicators reflect actual system state
- Only show "View Transcript" if transcript actually exists
- Only show "Processing" if capture is actually in progress

### Step 3: Fix Capture Endpoint (10 min)
- Investigate 422 error from capture endpoint
- Either fix the endpoint or provide better error handling
- Ensure capture button only appears when capture is actually possible

### Step 4: Add Sample Transcript Data (10 min)
- Create sample transcript data for testing
- Or remove transcript buttons for hearings without transcripts
- Ensure transcript pages work correctly

### Step 5: Test and Verify (5 min)
- Test all buttons and functionality
- Verify realistic dates are showing
- Ensure status indicators are accurate

## Expected Outcome
- Realistic hearing dates (e.g., recent dates in 2024/2025)
- Accurate status indicators reflecting actual system state
- Working capture buttons or proper error handling
- Transcript buttons only show when transcripts exist
- All UI elements function as expected

## Timeline: 40 minutes total