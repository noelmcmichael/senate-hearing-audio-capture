# Refocused Plan - Use Discovery System to Populate Database

**Problem**: Got stuck on database import when system already has discovery functionality
**Solution**: Use the built-in discovery system to populate database with real hearings

## 🎯 Actual Goal
- See discovered hearings in production
- Manually trigger processing of one hearing
- Validate end-to-end workflow works

## 💡 Key Insight
The system already has:
- ✅ Discovery endpoint: `POST /api/hearings/discover` (tested, returns 0 hearings)
- ✅ Congress API integration (just needs key authentication)
- ✅ Database tables and structure ready
- ✅ API endpoints functional

## 🚀 Simple 10-Minute Plan

### **Step 1: Fix Congress API Authentication (5 minutes)**
- The discovery system needs the Congress API key to work
- From previous session: API key works locally but fails in production
- Quick fix: Update the secret or environment variable

### **Step 2: Run Discovery (2 minutes)**
- Use the existing discovery endpoint to populate database
- `POST /api/hearings/discover` will find and save real hearings
- Much better than importing fake test data

### **Step 3: View & Test (3 minutes)**
- Check discovered hearings via API
- Pick one hearing to test manual processing
- Confirm workflow works

## 🔧 Implementation

### **Option A: Fix Congress API Key**
```bash
# Test current API key status
curl -X GET "https://senate-hearing-processor-518203250893.us-central1.run.app/api/health"

# If Congress API is issue, run discovery anyway - it might still work
curl -X POST "https://senate-hearing-processor-518203250893.us-central1.run.app/api/hearings/discover"
```

### **Option B: Admin Interface for Discovery**
- Create simple admin endpoint to trigger discovery
- Add manual controls for testing
- Better user experience than API calls

### **Option C: Skip Congress API Initially**
- Use committee website scraping only
- Discovery system has multiple sources
- Get hearings from committee pages directly

## 📋 Next Actions

1. **Test current discovery system** - see what it can find without fixing anything
2. **If it works**: Great! We have hearings to test
3. **If it doesn't**: Quick fix to Congress API key
4. **Focus on end goal**: Manual hearing processing test

## 🎉 This Approach is Better Because:
- **Real data**: Live hearings instead of fake test data
- **Uses existing functionality**: Discovery system already built
- **Faster**: No database import complexity
- **Production-ready**: Tests actual workflow

---

**Next Step**: Test discovery system as-is, then fix only what's needed