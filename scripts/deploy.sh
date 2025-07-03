#!/bin/bash
# Deployment script for Senate Hearing Audio Capture

set -e

# Configuration
PROJECT_ID=${GCP_PROJECT_ID}
REGION=${GCP_REGION:-us-central1}
SERVICE_NAME="senate-hearing-processor"
ENVIRONMENT=${ENVIRONMENT:-development}

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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI not found. Please install Google Cloud SDK."
        exit 1
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "docker not found. Please install Docker."
        exit 1
    fi
    
    # Check if terraform is installed
    if ! command -v terraform &> /dev/null; then
        log_error "terraform not found. Please install Terraform."
        exit 1
    fi
    
    # Check if authenticated with gcloud
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "No active gcloud authentication found. Please run 'gcloud auth login'."
        exit 1
    fi
    
    log_info "Prerequisites check passed."
}

# Set up GCP project
setup_gcp_project() {
    log_info "Setting up GCP project..."
    
    # Set project
    gcloud config set project $PROJECT_ID
    
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
        redis.googleapis.com
    
    log_info "GCP project setup completed."
}

# Build and push Docker image
build_and_push_image() {
    log_info "Building and pushing Docker image..."
    
    # Build image
    docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME:latest .
    
    # Configure Docker to use gcloud as a credential helper
    gcloud auth configure-docker --quiet
    
    # Push image
    docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:latest
    
    log_info "Docker image built and pushed successfully."
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    log_info "Deploying infrastructure with Terraform..."
    
    cd infrastructure/terraform
    
    # Initialize Terraform
    terraform init
    
    # Create terraform.tfvars if it doesn't exist
    if [ ! -f terraform.tfvars ]; then
        log_warn "terraform.tfvars not found. Creating from example..."
        cp terraform.tfvars.example terraform.tfvars
        log_error "Please edit terraform.tfvars with your configuration and run the script again."
        exit 1
    fi
    
    # Plan deployment
    terraform plan -var="project_id=$PROJECT_ID" -var="environment=$ENVIRONMENT"
    
    # Apply deployment
    terraform apply -var="project_id=$PROJECT_ID" -var="environment=$ENVIRONMENT" -auto-approve
    
    cd ../..
    
    log_info "Infrastructure deployed successfully."
}

# Deploy application to Cloud Run
deploy_application() {
    log_info "Deploying application to Cloud Run..."
    
    # Deploy to Cloud Run
    gcloud run deploy $SERVICE_NAME \
        --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --set-env-vars "ENV=$ENVIRONMENT" \
        --service-account $SERVICE_NAME@$PROJECT_ID.iam.gserviceaccount.com \
        --memory 4Gi \
        --cpu 2 \
        --concurrency 10 \
        --max-instances 10 \
        --timeout 3600
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
    
    log_info "Application deployed successfully."
    log_info "Service URL: $SERVICE_URL"
}

# Run health check
run_health_check() {
    log_info "Running health check..."
    
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
    
    # Wait for service to be ready
    sleep 30
    
    # Check health endpoint
    if curl -f "$SERVICE_URL/health" > /dev/null 2>&1; then
        log_info "Health check passed."
    else
        log_error "Health check failed."
        exit 1
    fi
}

# Main deployment function
main() {
    log_info "Starting deployment for environment: $ENVIRONMENT"
    
    check_prerequisites
    setup_gcp_project
    build_and_push_image
    deploy_infrastructure
    deploy_application
    run_health_check
    
    log_info "Deployment completed successfully!"
    log_info "Your application is running at: $(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')"
}

# Handle command line arguments
case "${1:-}" in
    "infrastructure")
        log_info "Deploying infrastructure only..."
        check_prerequisites
        setup_gcp_project
        deploy_infrastructure
        ;;
    "application")
        log_info "Deploying application only..."
        check_prerequisites
        build_and_push_image
        deploy_application
        run_health_check
        ;;
    "health")
        log_info "Running health check..."
        run_health_check
        ;;
    *)
        main
        ;;
esac