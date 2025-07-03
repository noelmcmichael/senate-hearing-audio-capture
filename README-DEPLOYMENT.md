# Senate Hearing Audio Capture - Deployment Guide

## Quick Start Deployment

### Prerequisites
- Google Cloud Platform account with billing enabled
- GitHub account
- Docker installed locally
- Terraform installed locally
- gcloud CLI installed and authenticated

### 1. GCP Project Setup (5 minutes)

```bash
# Run the automated setup script
./scripts/setup-gcp.sh YOUR_PROJECT_ID us-central1 YOUR_BILLING_ACCOUNT

# This will:
# - Create GCP project
# - Enable required APIs
# - Create service accounts
# - Set up IAM roles
# - Create storage buckets
# - Generate service account key
```

### 2. GitHub Repository Setup (5 minutes)

```bash
# Fork or create repository
git clone https://github.com/YOUR_USERNAME/senate-hearing-audio-capture.git
cd senate-hearing-audio-capture

# Add GitHub secrets (via GitHub web interface):
# - GCP_PROJECT_ID: your-project-id
# - GCP_SA_KEY: contents of service-account-key.json
```

### 3. Deploy Infrastructure (10 minutes)

```bash
# Deploy with Terraform
cd infrastructure/terraform
terraform init
terraform plan
terraform apply

# This creates:
# - Cloud SQL database
# - Redis instance
# - Cloud Storage buckets
# - Cloud Run service
# - Monitoring alerts
```

### 4. Deploy Application (5 minutes)

```bash
# Deploy application
./scripts/deploy.sh

# Or push to main branch for automatic deployment
git push origin main
```

## Manual Deployment Steps

### Phase 1: Infrastructure Setup

#### 1.1 Create GCP Project
```bash
# Create project
gcloud projects create YOUR_PROJECT_ID

# Set project
gcloud config set project YOUR_PROJECT_ID

# Link billing account
gcloud beta billing projects link YOUR_PROJECT_ID --billing-account=YOUR_BILLING_ACCOUNT
```

#### 1.2 Enable APIs
```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    monitoring.googleapis.com \
    logging.googleapis.com \
    storage.googleapis.com \
    redis.googleapis.com
```

#### 1.3 Create Service Account
```bash
# Create service account
gcloud iam service-accounts create senate-hearing-processor \
    --display-name="Senate Hearing Processor Service Account"

# Grant roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:senate-hearing-processor@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

# (Repeat for other required roles)
```

### Phase 2: Database Setup

#### 2.1 Create Cloud SQL Instance
```bash
gcloud sql instances create senate-hearing-db \
    --database-version=POSTGRES_13 \
    --region=us-central1 \
    --tier=db-f1-micro
```

#### 2.2 Create Database and User
```bash
gcloud sql databases create senate_hearing_db --instance=senate-hearing-db
gcloud sql users create app_user --instance=senate-hearing-db --password=SECURE_PASSWORD
```

### Phase 3: Storage Setup

#### 3.1 Create Storage Buckets
```bash
# Audio files bucket
gsutil mb -p YOUR_PROJECT_ID -l us-central1 gs://YOUR_PROJECT_ID-audio-files

# Backups bucket
gsutil mb -p YOUR_PROJECT_ID -l us-central1 gs://YOUR_PROJECT_ID-backups
```

### Phase 4: Redis Setup

#### 4.1 Create Redis Instance
```bash
gcloud redis instances create senate-hearing-cache \
    --size=1 \
    --region=us-central1 \
    --redis-version=redis_7_0
```

### Phase 5: Secrets Management

#### 5.1 Create Secrets
```bash
# Congress API key
echo "YOUR_CONGRESS_API_KEY" | gcloud secrets create congress-api-key --data-file=-

# Database password
echo "SECURE_DATABASE_PASSWORD" | gcloud secrets create database-password --data-file=-

# Application secret key
openssl rand -base64 32 | gcloud secrets create secret-key --data-file=-
```

### Phase 6: Application Deployment

#### 6.1 Build and Push Docker Image
```bash
# Build image
docker build -t gcr.io/YOUR_PROJECT_ID/senate-hearing-capture:latest .

# Push to registry
docker push gcr.io/YOUR_PROJECT_ID/senate-hearing-capture:latest
```

#### 6.2 Deploy to Cloud Run
```bash
gcloud run deploy senate-hearing-processor \
    --image gcr.io/YOUR_PROJECT_ID/senate-hearing-capture:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --service-account senate-hearing-processor@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --memory 4Gi \
    --cpu 2 \
    --timeout 3600
```

## Environment-Specific Configurations

### Development Environment
```bash
# Smaller resources for development
terraform apply -var="environment=development"

# This creates:
# - db-f1-micro database
# - 1GB Redis instance
# - 2 max Cloud Run instances
```

### Staging Environment
```bash
# Medium resources for staging
terraform apply -var="environment=staging"

# This creates:
# - db-g1-small database
# - 2GB Redis instance
# - 3 max Cloud Run instances
```

### Production Environment
```bash
# Full resources for production
terraform apply -var="environment=production"

# This creates:
# - db-custom-2-4096 database
# - 4GB Redis instance (HA)
# - 20 max Cloud Run instances
```

## Monitoring and Alerting

### Enable Monitoring
```bash
# Monitoring is automatically enabled with the infrastructure
# View metrics at: https://console.cloud.google.com/monitoring
```

### Set Up Alerts
```bash
# Alerts are automatically created via Terraform
# Configure notification channels in the console
```

## CI/CD Pipeline

### GitHub Actions
The `.github/workflows/ci-cd.yml` file provides:
- Automated testing on push
- Docker image building
- Deployment to staging and production
- Security scanning

### Manual Triggers
```bash
# Trigger deployment manually
gh workflow run ci-cd.yml --ref main
```

## Cost Optimization

### Development ($15-30/month)
- db-f1-micro: $7/month
- Redis Basic 1GB: $5/month
- Cloud Run (minimal usage): $5/month
- Storage: $2/month

### Production ($60-125/month)
- db-custom-2-4096: $40/month
- Redis HA 4GB: $30/month
- Cloud Run (moderate usage): $30/month
- Storage: $15/month

## Security Best Practices

### 1. IAM Roles
- Use least privilege principle
- Separate service accounts for different functions
- Regular audit of permissions

### 2. Secrets Management
- All secrets in Secret Manager
- No hardcoded credentials
- Automatic rotation where possible

### 3. Network Security
- VPC configuration for database
- Private IP for Redis
- Cloud Run with authenticated endpoints

### 4. Data Security
- Encryption at rest and in transit
- Secure database connections
- Regular security updates

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues
```bash
# Check Cloud SQL status
gcloud sql instances describe senate-hearing-db

# Check service account permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID
```

#### 2. Cloud Run Deployment Issues
```bash
# Check deployment status
gcloud run services describe senate-hearing-processor --region us-central1

# View logs
gcloud logs tail --follow
```

#### 3. Secret Access Issues
```bash
# Check secret permissions
gcloud secrets get-iam-policy congress-api-key

# Test secret access
gcloud secrets versions access latest --secret="congress-api-key"
```

### Health Checks
```bash
# Check application health
curl https://YOUR_SERVICE_URL/health

# Check detailed health
curl https://YOUR_SERVICE_URL/health/detailed

# Run production tests
python tests/production_test_suite.py --url https://YOUR_SERVICE_URL
```

## Scaling Considerations

### Horizontal Scaling
- Cloud Run auto-scales based on traffic
- Configure max instances based on expected load
- Use concurrency settings to optimize resource usage

### Vertical Scaling
- Increase CPU/memory for Cloud Run instances
- Upgrade database tier for higher performance
- Increase Redis memory for larger cache

### Cost vs Performance
- Monitor actual usage patterns
- Adjust instance sizes based on metrics
- Use Cloud Monitoring to optimize configuration

## Maintenance

### Regular Tasks
- Monitor application metrics
- Review and rotate secrets
- Update dependencies
- Review and optimize costs

### Backup Strategy
- Database backups (automated)
- Application configuration backups
- Audio files lifecycle management

### Updates
- Use CI/CD for automated deployments
- Test updates in staging first
- Monitor post-deployment metrics

## Support

### Monitoring
- Application metrics: Available in Google Cloud Monitoring
- Custom dashboards: Available in `monitoring/` directory
- Alerting: Configured via Terraform

### Logging
- Application logs: Available in Google Cloud Logging
- Structured logging: JSON format for better parsing
- Log levels: Configurable via environment variables

### Performance
- Response time monitoring
- Database query performance
- Processing queue metrics
- Error rate tracking

---

For additional support, refer to:
- [Google Cloud Documentation](https://cloud.google.com/docs)
- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)