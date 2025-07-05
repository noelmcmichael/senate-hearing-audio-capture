# Database Persistence Fix - Senate Hearing Audio Capture

## 🚨 Critical Issue Identified

**Problem**: SQLite database is ephemeral in Cloud Run - data is lost when service restarts
**Impact**: Committees and hearings disappear, causing frontend to show empty state
**Current Status**: Manual bootstrap required after every service restart

## 🔧 Immediate Solutions

### Option 1: Auto-Bootstrap on Startup (Quick Fix)
Add startup check to automatically bootstrap database when empty.

**Implementation**:
```python
# Add to main application startup
@app.on_event("startup")
async def startup_event():
    """Auto-bootstrap database if empty."""
    db = get_enhanced_db()
    
    # Check if database is empty
    committees_count = db.get_committees_count()
    
    if committees_count == 0:
        logger.info("Database is empty - running auto-bootstrap")
        await bootstrap_system()
        logger.info("Auto-bootstrap completed")
```

### Option 2: Cloud Storage Backup (Medium Fix)
Backup/restore SQLite database to/from Cloud Storage.

**Implementation**:
```python
# Backup database to Cloud Storage on changes
# Restore database from Cloud Storage on startup
async def backup_database():
    """Backup SQLite database to Cloud Storage."""
    # Upload database file to GCS bucket
    
async def restore_database():
    """Restore SQLite database from Cloud Storage."""
    # Download database file from GCS bucket
```

### Option 3: Cloud SQL Migration (Long-term Fix)
Migrate to Google Cloud SQL PostgreSQL for true persistence.

**Benefits**:
- True database persistence
- Better performance and scalability
- Automatic backups and high availability
- No data loss on service restarts

## 🎯 Recommended Approach

### Phase 1: Immediate Fix (5 minutes)
1. Add auto-bootstrap on startup
2. Add health check endpoint that triggers bootstrap if needed
3. Test with service restart

### Phase 2: Medium-term Fix (30 minutes)
1. Implement Cloud Storage backup/restore
2. Add periodic database backups
3. Test persistence across restarts

### Phase 3: Long-term Fix (60 minutes)
1. Setup Cloud SQL PostgreSQL instance
2. Migrate schema and data
3. Update application configuration
4. Deploy with persistent database

## 🚀 Implementation Plan

### Step 1: Auto-Bootstrap Fix
```bash
# Add startup event handler to FastAPI application
# Modify main_app.py to include auto-bootstrap
# Test with manual service restart
```

### Step 2: Test Persistence
```bash
# Deploy updated application
# Verify auto-bootstrap works
# Test frontend displays committees after restart
```

### Step 3: Monitor and Validate
```bash
# Monitor service logs for auto-bootstrap events
# Verify frontend stability
# Plan for Cloud SQL migration
```

## 📋 Files to Modify

1. **src/api/main_app.py**: Add startup event handler
2. **src/api/database_enhanced.py**: Add auto-bootstrap logic
3. **cloudbuild.yaml**: Ensure build includes database initialization
4. **requirements.txt**: Add any additional dependencies

## 🔍 Testing Strategy

1. **Local Testing**: Verify auto-bootstrap works locally
2. **Staging Testing**: Test with Cloud Run service restart
3. **Production Testing**: Monitor logs and frontend behavior
4. **Performance Testing**: Ensure startup time is acceptable

## 📊 Expected Outcomes

- **Database Persistence**: Data survives service restarts
- **Frontend Stability**: No more empty committee lists
- **User Experience**: Consistent data availability
- **Operational Reliability**: Reduced manual intervention

## 🚨 Risks and Mitigation

**Risk**: Auto-bootstrap on every startup
**Mitigation**: Check database state before bootstrapping

**Risk**: Bootstrap conflicts with existing data
**Mitigation**: Use INSERT OR REPLACE statements

**Risk**: Startup time increase
**Mitigation**: Optimize bootstrap process, consider async execution

## 💡 Next Steps

1. Implement auto-bootstrap fix
2. Test with current deployment
3. Verify frontend shows committees consistently
4. Plan Cloud SQL migration for permanent solution