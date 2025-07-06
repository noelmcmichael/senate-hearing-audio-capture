# Step-by-Step Fix Plan: UI Field Mapping Issue

## Problem Identified
The frontend Dashboard.js expects field names that don't match the API response:
- API returns: `title`, `date`, `type`
- Frontend expects: `hearing_title`, `hearing_date`, `hearing_type`

## Root Cause
The enhanced title display logic in `getDisplayTitle()` checks `hearing.hearing_title` but the API returns `hearing.title`.

## Solution Steps

### Step 1: Fix Field Mapping in Dashboard.js (5 min)
- Update `getDisplayTitle()` to check `hearing.title` instead of `hearing.hearing_title`
- Update `formatDate()` calls to use `hearing.date` instead of `hearing.hearing_date`
- Update `getHearingType()` to use `hearing.type` instead of `hearing.hearing_type`
- Update search filter to use correct field names

### Step 2: Test Enhanced Titles Locally (5 min)
- Start local dev server
- Verify enhanced titles are displayed correctly
- Test bootstrap entry detection logic

### Step 3: Deploy Fixed Frontend (5 min)
- Build React app with fixes
- Build Docker container
- Deploy to Cloud Run

### Step 4: Verify Production Fix (5 min)
- Test production URL
- Confirm enhanced titles are displayed
- Verify capture buttons work
- Document successful resolution

## Expected Outcome
- Committee hearings will show enhanced titles:
  - SCOM: "Artificial Intelligence in Transportation: Opportunities and Challenges"
  - SSCI: "Foreign Election Interference and Social Media Platforms"
  - SSJU: "Judicial Nomination: District Court Appointments"
- Capture buttons will remain functional
- Status variety will work correctly

## Timeline: 20 minutes total