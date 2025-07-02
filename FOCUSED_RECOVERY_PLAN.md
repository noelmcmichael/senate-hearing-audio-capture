# Focused Recovery Plan: Making the App Actually Work

## 🚨 **Core Problems Identified**
1. **Modal Rendering Issue**: Details modal doesn't show properly
2. **Capture Button Broken**: No visible action when clicked
3. **Confusing UX**: Conflicting status messages and unclear user journey
4. **Data Inconsistencies**: Mock vs real data causing confusion
5. **Missing Integration**: Transcripts disconnected from hearings

## 🎯 **Recovery Strategy: 3-Phase Approach**

### **Phase 1: Fix Core Functionality (30 min)**
**Goal**: Make the essential features actually work

1. **Fix Modal Rendering** (5 min)
   - Fix React warnings causing modal issues
   - Ensure modal appears immediately when clicked

2. **Fix Capture Button** (10 min)  
   - Connect to real API endpoint
   - Show immediate feedback (loading state)
   - Display success/error messages

3. **Fix Data Flow** (10 min)
   - Remove mock data confusion
   - Use consistent real data throughout
   - Fix pipeline status accuracy

4. **Clean Console Errors** (5 min)
   - Fix React warnings
   - Clean up component code

### **Phase 2: Simplify UX (20 min)**
**Goal**: Create a coherent user experience

1. **Consistent Status Logic** (10 min)
   - One source of truth for hearing status
   - Clear action buttons based on actual state
   - Remove conflicting messages

2. **Integrate Transcripts** (10 min)
   - Add "View Transcript" button to hearing details
   - Show transcript availability in hearing lists
   - Direct links from hearings to transcripts

### **Phase 3: Coherent User Journey (20 min)**
**Goal**: Clear path for users to accomplish tasks

1. **Streamlined Navigation** (10 min)
   - Clear entry points for main tasks
   - Breadcrumb navigation
   - Consistent actions across views

2. **Real Functionality Demo** (10 min)
   - Working capture process
   - Actual transcript generation
   - Visible progress tracking

## 🎯 **Success Criteria**
- Click "View Details" → Modal appears immediately
- Click "Capture Audio" → See loading state → Get success/error feedback
- Pipeline status matches actual hearing state
- Transcripts accessible from hearing details
- No console errors
- Clear user journey: Browse → Details → Action → Result

## ⏱️ **Timeline**: 70 minutes total
**Outcome**: Working core functionality with coherent UX