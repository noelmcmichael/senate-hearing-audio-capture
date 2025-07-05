# Infrastructure Fix Plan - Production Environment

## 🎯 **Objective**
Fix the 4 critical infrastructure issues to achieve full production functionality (60% → 100%)

## 📋 **Issues to Fix**

### **1. GCS Storage Permissions (Critical)**
**Problem**: Service account missing storage.buckets.get permission
**Error**: `403 GET https://storage.googleapis.com/storage/v1/b/senate-hearing-capture-audio-files-development`
**Impact**: Audio file storage/retrieval not available
**Solution**: Add storage permissions to service account

### **2. Redis Connection (Critical)**
**Problem**: Connection timeout to Redis server
**Error**: `Timeout connecting to server`
**Impact**: Session management and caching not available
**Solution**: Configure Redis instance or disable Redis features

### **3. Congress API Key (Important)**
**Problem**: Invalid API key for Congress.gov
**Error**: `API_KEY_INVALID`
**Impact**: Official congressional data sync not available
**Solution**: Update with valid Congress.gov API key from secrets

### **4. Database Population (Important)**
**Problem**: Empty database - no committees or hearings
**Error**: `total_committees: 0, total_hearings: 0`
**Impact**: No data for testing or processing
**Solution**: Populate with test committee and hearing data

## 🚀 **Implementation Plan**

### **Step 1: GCS Permissions Fix (10 minutes) ✅ COMPLETE**
- [x] Check current service account permissions
- [x] Add storage.buckets.get permission (roles/storage.objectAdmin)
- [x] Add storage.objects.get permission (roles/storage.legacyBucketReader)
- [x] Add storage.objects.create permission (included in objectAdmin)
- [x] Test GCS connectivity - ✅ WORKING: {"status": "healthy", "response_time": 0.092}

### **Step 2: Redis Configuration (5 minutes) ⚠️ NETWORK ISSUE**
- [x] Check Redis instance status - ✅ RUNNING: READY state at 10.187.135.99:6379
- [x] Configure Redis connection string - ✅ CONFIGURED: redis://10.187.135.99:6379
- [ ] Fix VPC connector for Cloud Run to access private Redis
- [x] Test Redis connectivity - ❌ FAILING: "Timeout connecting to server"
- **Issue**: Cloud Run needs VPC connector to access private Redis instance

### **Step 3: Congress API Key (5 minutes) ⚠️ STILL INVALID**
- [x] Retrieve valid Congress.gov API key from secrets - ✅ FOUND: Local key working
- [x] Update GCP Secret Manager with valid key - ✅ UPDATED: Version 4 deployed
- [x] Test Congress API connectivity - ❌ FAILING: "API_KEY_INVALID"
- [ ] Debug API key deployment issue
- **Issue**: Key works locally but fails in production - possible encoding/deployment issue

### **Step 4: Database Population (10 minutes) ⚠️ BLOCKED BY CONGRESS API**
- [x] Create test committee data - ✅ PREPARED: 3 committees ready
- [x] Create test hearing data - ✅ PREPARED: 2 hearings ready
- [ ] Populate production database - ❌ BLOCKED: Discovery endpoint needs Congress API
- [ ] Test API endpoints with data - ❌ PENDING: Database population
- [ ] Verify stats endpoint functionality - ❌ FAILING: "unsupported operand type(s) for +: 'NoneType' and 'NoneType'"
- **Issue**: Discovery system depends on Congress API for data population

## 🔧 **Technical Implementation**

### **GCS Permissions**
```bash
# Check current permissions
gcloud projects get-iam-policy senate-hearing-capture

# Add storage permissions
gcloud projects add-iam-policy-binding senate-hearing-capture \
  --member="serviceAccount:senate-hearing-processor@senate-hearing-capture.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

### **Redis Configuration**
```bash
# Check Redis instances
gcloud redis instances list --project=senate-hearing-capture

# Get Redis connection info
gcloud redis instances describe redis-instance-name --region=us-central1
```

### **Congress API Key**
```bash
# Update secret with valid key
gcloud secrets versions add congress-api-key --data-file=api_key.txt
```

### **Database Population**
```python
# Populate test data
python -c "
from src.api.database_enhanced import get_enhanced_db
# Add test committees and hearings
"
```

## 📊 **Success Metrics**

### **Before Fix**
- Database: ✅ Healthy
- Redis: ❌ Connection timeout
- Storage: ❌ Permission denied
- Processing: ✅ Components available
- **Overall**: 50% infrastructure health

### **After Fix Target**
- Database: ✅ Healthy
- Redis: ✅ Connected
- Storage: ✅ Accessible
- Processing: ✅ Components available
- **Overall**: 100% infrastructure health

## 🎯 **Validation Tests**

### **Test 1: Storage Health**
```bash
curl -s https://senate-hearing-processor-518203250893.us-central1.run.app/health/storage | jq .
# Expected: {"status": "healthy"}
```

### **Test 2: Redis Health**
```bash
curl -s https://senate-hearing-processor-518203250893.us-central1.run.app/health/redis | jq .
# Expected: {"status": "healthy"}
```

### **Test 3: Congress API**
```bash
curl -s https://senate-hearing-processor-518203250893.us-central1.run.app/api/test/congress | jq .
# Expected: {"overall_status": {"success": true}}
```

### **Test 4: Database Content**
```bash
curl -s https://senate-hearing-processor-518203250893.us-central1.run.app/api/committees | jq .
# Expected: {"total_committees": > 0}
```

### **Test 5: Stats Endpoint**
```bash
curl -s https://senate-hearing-processor-518203250893.us-central1.run.app/api/stats | jq .
# Expected: Valid stats object without errors
```

## ⏰ **Timeline**
- **Total Duration**: 30 minutes
- **Step 1**: 10 minutes (GCS permissions)
- **Step 2**: 5 minutes (Redis configuration)
- **Step 3**: 5 minutes (Congress API key)
- **Step 4**: 10 minutes (Database population)

## 🎉 **Expected Outcome**
- **Production Readiness**: 60% → 100%
- **Infrastructure Health**: 50% → 100%
- **API Functionality**: Full system operational
- **Ready for**: End-to-end testing and user workflows

---

**Ready to begin implementation**: All steps documented and ready for execution