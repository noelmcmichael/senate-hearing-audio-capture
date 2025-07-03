#!/bin/bash
# GCP setup script for Senate Hearing Audio Capture

set -e

# Configuration
PROJECT_ID=${1:-}
REGION=${2:-us-central1}
BILLING_ACCOUNT=${3:-}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if project ID is provided
if [ -z "$PROJECT_ID" ]; then
    log_error "Usage: $0 <PROJECT_ID> [REGION] [BILLING_ACCOUNT]"
    log_error "Example: $0 my-senate-hearing-project us-central1 012345-678901-234567"
    exit 1
fi

log_info "Setting up GCP project: $PROJECT_ID"
log_info "Region: $REGION"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    log_error "gcloud CLI not found. Please install Google Cloud SDK."
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    log_error "No active gcloud authentication found. Please run 'gcloud auth login'."
    exit 1
fi

# Create project if it doesn't exist
log_info "Creating GCP project..."
if ! gcloud projects describe $PROJECT_ID &> /dev/null; then
    gcloud projects create $PROJECT_ID
    log_info "Project $PROJECT_ID created successfully."
else
    log_info "Project $PROJECT_ID already exists."
fi

# Set project
gcloud config set project $PROJECT_ID

# Link billing account if provided
if [ -n "$BILLING_ACCOUNT" ]; then
    log_info "Linking billing account..."
    gcloud beta billing projects link $PROJECT_ID --billing-account=$BILLING_ACCOUNT
fi

# Enable required APIs
log_info "Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    monitoring.googleapis.com \
    logging.googleapis.com \
    storage.googleapis.com \
    container.googleapis.com \
    cloudscheduler.googleapis.com \
    redis.googleapis.com \
    compute.googleapis.com \
    servicenetworking.googleapis.com

# Create service account
log_info "Creating service account..."
SERVICE_ACCOUNT_NAME="senate-hearing-processor"
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL &> /dev/null; then
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="Senate Hearing Processor Service Account" \
        --description="Service account for Senate Hearing Audio Capture application"
    log_info "Service account created: $SERVICE_ACCOUNT_EMAIL"
else
    log_info "Service account already exists: $SERVICE_ACCOUNT_EMAIL"
fi

# Grant necessary IAM roles
log_info "Granting IAM roles..."
ROLES=(
    "roles/cloudsql.client"
    "roles/secretmanager.secretAccessor"
    "roles/storage.objectAdmin"
    "roles/monitoring.metricWriter"
    "roles/logging.logWriter"
    "roles/redis.editor"
    "roles/cloudbuild.builds.builder"
    "roles/run.developer"
)

for role in "${ROLES[@]}"; do
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="$role"
done

# Create storage bucket for Terraform state
log_info "Creating Terraform state bucket..."
STATE_BUCKET="$PROJECT_ID-terraform-state"
if ! gsutil ls gs://$STATE_BUCKET &> /dev/null; then
    gsutil mb -p $PROJECT_ID -l $REGION gs://$STATE_BUCKET
    gsutil versioning set on gs://$STATE_BUCKET
    log_info "Terraform state bucket created: gs://$STATE_BUCKET"
else
    log_info "Terraform state bucket already exists: gs://$STATE_BUCKET"
fi

# Create service account key for GitHub Actions
log_info "Creating service account key for CI/CD..."
KEY_FILE="$PROJECT_ID-service-account-key.json"
if [ ! -f "$KEY_FILE" ]; then
    gcloud iam service-accounts keys create $KEY_FILE \
        --iam-account=$SERVICE_ACCOUNT_EMAIL
    log_info "Service account key created: $KEY_FILE"
    log_warn "Add this key to your GitHub repository secrets as GCP_SA_KEY"
else
    log_info "Service account key already exists: $KEY_FILE"
fi

# Create initial secrets
log_info "Creating initial secrets..."

# Create placeholder for Congress API key
if ! gcloud secrets describe congress-api-key &> /dev/null; then
    echo "PLACEHOLDER_CONGRESS_API_KEY" | gcloud secrets create congress-api-key --data-file=-
    log_info "Congress API key secret created (placeholder)"
    log_warn "Update the Congress API key secret with your actual key"
else
    log_info "Congress API key secret already exists"
fi

# Create random secret key
if ! gcloud secrets describe secret-key &> /dev/null; then
    openssl rand -base64 32 | gcloud secrets create secret-key --data-file=-
    log_info "Secret key created"
else
    log_info "Secret key already exists"
fi

# Set up Cloud Build trigger (optional)
log_info "Setting up Cloud Build trigger..."
if ! gcloud builds triggers describe github-trigger &> /dev/null; then
    log_info "Cloud Build trigger not found. You'll need to set this up manually in the console."
    log_info "Go to: https://console.cloud.google.com/cloud-build/triggers"
else
    log_info "Cloud Build trigger already exists"
fi

# Create terraform.tfvars file
log_info "Creating terraform.tfvars file..."
cat > infrastructure/terraform/terraform.tfvars << EOF
project_id = "$PROJECT_ID"
region = "$REGION"
environment = "production"
notification_email = "$(gcloud auth list --filter=status:ACTIVE --format="value(account)")"
EOF

log_info "Terraform configuration created"

# Summary
log_info "GCP setup completed successfully!"
echo ""
echo "=== SETUP SUMMARY ==="
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service Account: $SERVICE_ACCOUNT_EMAIL"
echo "Terraform State Bucket: gs://$STATE_BUCKET"
echo "Service Account Key: $KEY_FILE"
echo ""
echo "=== NEXT STEPS ==="
echo "1. Add the service account key to your GitHub repository secrets:"
echo "   - Go to your GitHub repository settings"
echo "   - Add a new secret named 'GCP_SA_KEY'"
echo "   - Paste the contents of $KEY_FILE"
echo ""
echo "2. Add your project ID to GitHub repository secrets:"
echo "   - Add a new secret named 'GCP_PROJECT_ID'"
echo "   - Set the value to: $PROJECT_ID"
echo ""
echo "3. Update the Congress API key secret:"
echo "   gcloud secrets versions add congress-api-key --data-file=<your-api-key-file>"
echo ""
echo "4. Deploy the infrastructure:"
echo "   cd infrastructure/terraform"
echo "   terraform init"
echo "   terraform plan"
echo "   terraform apply"
echo ""
echo "5. Deploy the application:"
echo "   ./scripts/deploy.sh"
echo ""
log_info "Setup complete!"