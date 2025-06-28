# Committee Expansion Plan
*Congress.gov API Integration - Phase 4*

## 🎯 Objective
Expand official Congress.gov API integration from 1 committee (Commerce) to comprehensive coverage of priority Senate committees, focusing on ISVP-compatible committees first.

## 📊 Current State
- **API Integration**: Working with Commerce Committee (1/10)
- **ISVP Compatible**: 4 committees tested for audio capture
- **Committee Mappings**: 6 committees configured in congress_sync.py
- **Manual Sync**: Working system ready for expansion

## 🗺️ Expansion Strategy

### Phase 4A: Priority ISVP-Compatible Committees
Focus on committees with confirmed audio capture capability:

1. **Intelligence** (Priority 2)
   - System Code: `slin00`
   - Chamber: Senate
   - Status: ISVP tested ✅

2. **Banking** (Priority 3)  
   - System Code: `ssbk00`
   - Chamber: Senate
   - Status: ISVP tested ✅

3. **Judiciary** (Priority 4)
   - System Code: `ssju00` 
   - Chamber: Senate
   - Status: ISVP tested ✅

### Phase 4B: Additional Senate Committees
Expand to remaining Senate committees:

4. **Finance** (Priority 5)
   - System Code: `ssfi00`
   - Chamber: Senate
   - Status: Not tested, high priority

5. **Armed Services** (Priority 6)
   - System Code: `ssas00`
   - Chamber: Senate
   - Status: Not tested

6. **HELP** (Health, Education, Labor, Pensions) (Priority 7)
   - System Code: `sshe00`
   - Chamber: Senate
   - Status: Not tested

### Phase 4C: High-Value House Committees
Add key House committees for comprehensive coverage:

7. **House Financial Services**
   - System Code: `hsba00`
   - Chamber: House
   - Status: Already mapped ✅

8. **House Judiciary** 
   - System Code: `hsju00`
   - Chamber: House
   - Status: Already mapped ✅

## 🔧 Technical Implementation Tasks

### 1. Enhanced Committee Mapping (30 min)
- [ ] Add missing system codes to congress_sync.py
- [ ] Verify official committee names
- [ ] Update committee mappings with additional metadata

### 2. Batch Sync Optimization (45 min)
- [ ] Implement efficient member filtering by committee
- [ ] Add committee membership detection logic
- [ ] Optimize API requests for multiple committees

### 3. Enhanced Member Detection (60 min)
- [ ] Improve committee member identification
- [ ] Add leadership role detection (Chair, Ranking Member)
- [ ] Enhance alias generation for better speaker ID

### 4. Validation and Testing (30 min)
- [ ] Create committee sync verification tests
- [ ] Test member data quality across committees
- [ ] Validate transcript enrichment compatibility

## 📈 Success Metrics
- **Committee Coverage**: From 1 to 8 committees (800% increase)
- **Member Coverage**: From ~25 to ~200+ congressional members
- **ISVP Integration**: 4/4 compatible committees with official data
- **Data Quality**: Government-verified metadata for all committees

## 🛠️ Implementation Order
1. **Update committee mappings** with missing system codes
2. **Sync Intelligence Committee** (highest priority ISVP-compatible)
3. **Sync Banking Committee** (Priority 3)
4. **Sync Judiciary Committee** (Priority 4)
5. **Validate enrichment** with expanded member data
6. **Extend to additional committees** as needed

## 📋 Quality Gates
- [ ] API sync successful for each committee
- [ ] Member count reasonable (10-25 per committee)
- [ ] Speaker identification working with new aliases
- [ ] No data corruption in existing committees

## 💡 Key Decisions
- **Manual sync approach**: Keep manual kickoff as user suggested
- **ISVP priority**: Focus on audio-capture compatible committees first
- **Quality over quantity**: Ensure each committee is properly validated
- **Backward compatibility**: Maintain existing functionality

---
*Ready to proceed with systematic committee expansion*