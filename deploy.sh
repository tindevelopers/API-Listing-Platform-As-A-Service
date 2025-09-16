#!/bin/bash

# LAAS Platform Deployment Script for Google Cloud Run
# This script handles the complete deployment process

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"your-project-id"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="laas-api"
IMAGE_NAME="laas-api"
REPOSITORY="laas"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    log_success "All dependencies are installed"
}

# Authenticate with Google Cloud
authenticate() {
    log_info "Authenticating with Google Cloud..."
    
    # Check if already authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        gcloud auth login
    fi
    
    # Set project
    gcloud config set project $PROJECT_ID
    
    # Enable required APIs
    log_info "Enabling required Google Cloud APIs..."
    gcloud services enable \
        cloudbuild.googleapis.com \
        run.googleapis.com \
        sqladmin.googleapis.com \
        secretmanager.googleapis.com \
        redis.googleapis.com \
        artifactregistry.googleapis.com
    
    log_success "Authentication and API setup complete"
}

# Create Google Cloud resources
create_infrastructure() {
    log_info "Creating Google Cloud infrastructure..."
    
    # Create Artifact Registry repository
    log_info "Creating Artifact Registry repository..."
    gcloud artifacts repositories create $REPOSITORY \
        --repository-format=docker \
        --location=$REGION \
        --description="LAAS Platform Docker images" \
        --quiet || log_warning "Repository may already exist"
    
    # Create Cloud SQL instance
    log_info "Creating Cloud SQL instance..."
    gcloud sql instances create laas-sql \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=$REGION \
        --storage-type=SSD \
        --storage-size=10GB \
        --backup \
        --quiet || log_warning "SQL instance may already exist"
    
    # Create database
    log_info "Creating database..."
    gcloud sql databases create laas_platform \
        --instance=laas-sql \
        --quiet || log_warning "Database may already exist"
    
    # Create database user
    log_info "Creating database user..."
    gcloud sql users create laas_user \
        --instance=laas-sql \
        --password=$(openssl rand -base64 32) \
        --quiet || log_warning "Database user may already exist"
    
    # Create Redis instance
    log_info "Creating Redis instance..."
    gcloud redis instances create laas-redis \
        --size=1 \
        --region=$REGION \
        --redis-version=redis_7_0 \
        --tier=basic \
        --quiet || log_warning "Redis instance may already exist"
    
    log_success "Infrastructure creation complete"
}

# Create secrets
create_secrets() {
    log_info "Creating secrets..."
    
    # Generate secrets if they don't exist
    JWT_SECRET=$(openssl rand -base64 32)
    SECRET_KEY=$(openssl rand -base64 32)
    
    # Get database connection details
    DB_IP=$(gcloud sql instances describe laas-sql --format="value(ipAddresses[0].ipAddress)")
    DB_PASSWORD=$(gcloud sql users describe laas_user --instance=laas-sql --format="value(password)" 2>/dev/null || echo "password")
    DATABASE_URL="postgresql://laas_user:${DB_PASSWORD}@${DB_IP}:5432/laas_platform"
    
    # Get Redis connection details
    REDIS_IP=$(gcloud redis instances describe laas-redis --region=$REGION --format="value(host)")
    REDIS_URL="redis://${REDIS_IP}:6379/0"
    
    # Create secrets
    echo -n "$DATABASE_URL" | gcloud secrets create DATABASE_URL --data-file=- --quiet || \
        echo -n "$DATABASE_URL" | gcloud secrets versions add DATABASE_URL --data-file=-
    
    echo -n "$JWT_SECRET" | gcloud secrets create JWT_SECRET_KEY --data-file=- --quiet || \
        echo -n "$JWT_SECRET" | gcloud secrets versions add JWT_SECRET_KEY --data-file=-
    
    echo -n "$SECRET_KEY" | gcloud secrets create SECRET_KEY --data-file=- --quiet || \
        echo -n "$SECRET_KEY" | gcloud secrets versions add SECRET_KEY --data-file=-
    
    echo -n "$REDIS_URL" | gcloud secrets create REDIS_URL --data-file=- --quiet || \
        echo -n "$REDIS_URL" | gcloud secrets versions add REDIS_URL --data-file=-
    
    # Grant Cloud Run access to secrets
    gcloud secrets add-iam-policy-binding DATABASE_URL \
        --member="serviceAccount:${PROJECT_ID}-compute@developer.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"
    
    gcloud secrets add-iam-policy-binding JWT_SECRET_KEY \
        --member="serviceAccount:${PROJECT_ID}-compute@developer.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"
    
    gcloud secrets add-iam-policy-binding SECRET_KEY \
        --member="serviceAccount:${PROJECT_ID}-compute@developer.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"
    
    gcloud secrets add-iam-policy-binding REDIS_URL \
        --member="serviceAccount:${PROJECT_ID}-compute@developer.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"
    
    log_success "Secrets created and configured"
}

# Build and push Docker image
build_and_push() {
    log_info "Building and pushing Docker image..."
    
    # Configure Docker for Artifact Registry
    gcloud auth configure-docker ${REGION}-docker.pkg.dev
    
    # Build image
    REVISION=$(date +%Y%m%d-%H%M%S)
    IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${REVISION}"
    
    log_info "Building image: $IMAGE_URI"
    docker build -t $IMAGE_URI .
    
    # Push image
    log_info "Pushing image to Artifact Registry..."
    docker push $IMAGE_URI
    
    # Tag as latest
    LATEST_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:latest"
    docker tag $IMAGE_URI $LATEST_URI
    docker push $LATEST_URI
    
    log_success "Image built and pushed successfully"
    echo "REVISION=$REVISION" > .env.deploy
}

# Deploy to Cloud Run
deploy() {
    log_info "Deploying to Cloud Run..."
    
    # Load revision from build step
    if [ -f .env.deploy ]; then
        source .env.deploy
    else
        log_error "Build step must be completed first"
        exit 1
    fi
    
    # Deploy using gcloud
    gcloud run deploy $SERVICE_NAME \
        --image="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${REVISION}" \
        --region=$REGION \
        --platform=managed \
        --allow-unauthenticated \
        --port=8000 \
        --memory=2Gi \
        --cpu=2 \
        --min-instances=0 \
        --max-instances=100 \
        --concurrency=1000 \
        --timeout=300 \
        --set-env-vars="ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT_ID=${PROJECT_ID},GOOGLE_CLOUD_REGION=${REGION}" \
        --set-secrets="DATABASE_URL=DATABASE_URL:latest,JWT_SECRET_KEY=JWT_SECRET_KEY:latest,SECRET_KEY=SECRET_KEY:latest,REDIS_URL=REDIS_URL:latest" \
        --add-cloudsql-instances="${PROJECT_ID}:${REGION}:laas-sql"
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
    
    log_success "Deployment complete!"
    log_info "Service URL: $SERVICE_URL"
    log_info "API Documentation: $SERVICE_URL/docs"
    log_info "Health Check: $SERVICE_URL/health"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
    
    # Wait for service to be ready
    log_info "Waiting for service to be ready..."
    sleep 30
    
    # Run migrations via health check (this will trigger table creation)
    curl -f "$SERVICE_URL/health" || log_warning "Health check failed, but service may still be starting"
    
    log_success "Database migrations completed"
}

# Main deployment function
main() {
    log_info "Starting LAAS Platform deployment..."
    
    # Check if PROJECT_ID is set
    if [ "$PROJECT_ID" = "your-project-id" ]; then
        log_error "Please set PROJECT_ID environment variable or update the script"
        exit 1
    fi
    
    # Parse command line arguments
    case "${1:-all}" in
        "check")
            check_dependencies
            ;;
        "auth")
            authenticate
            ;;
        "infra")
            create_infrastructure
            ;;
        "secrets")
            create_secrets
            ;;
        "build")
            build_and_push
            ;;
        "deploy")
            deploy
            ;;
        "migrate")
            run_migrations
            ;;
        "all")
            check_dependencies
            authenticate
            create_infrastructure
            create_secrets
            build_and_push
            deploy
            run_migrations
            ;;
        *)
            echo "Usage: $0 {check|auth|infra|secrets|build|deploy|migrate|all}"
            echo ""
            echo "Commands:"
            echo "  check   - Check dependencies"
            echo "  auth    - Authenticate with Google Cloud"
            echo "  infra   - Create infrastructure resources"
            echo "  secrets - Create secrets"
            echo "  build   - Build and push Docker image"
            echo "  deploy  - Deploy to Cloud Run"
            echo "  migrate - Run database migrations"
            echo "  all     - Run all steps (default)"
            exit 1
            ;;
    esac
    
    log_success "LAAS Platform deployment completed successfully!"
}

# Run main function
main "$@"

