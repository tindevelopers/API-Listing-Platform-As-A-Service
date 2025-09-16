#!/bin/bash

# GitHub Actions Secrets Setup Script for LAAS Platform
# This script helps you set up the required secrets in your GitHub repository

echo "🔐 GitHub Actions Secrets Setup for LAAS Platform"
echo "=================================================="
echo ""

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed."
    echo "Please install it first: brew install gh"
    echo "Then authenticate: gh auth login"
    exit 1
fi

# Check if user is authenticated with GitHub
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub CLI."
    echo "Please run: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI is installed and authenticated"
echo ""

# Get repository information
REPO_URL=$(git remote get-url origin 2>/dev/null)
if [[ $REPO_URL == *"github.com"* ]]; then
    REPO_NAME=$(echo $REPO_URL | sed 's/.*github.com[:/]\([^/]*\/[^/]*\)\.git.*/\1/')
    echo "📁 Repository: $REPO_NAME"
else
    echo "❌ This doesn't appear to be a GitHub repository"
    echo "Please make sure you're in a Git repository with a GitHub remote"
    exit 1
fi

echo ""
echo "🔑 Setting up GitHub Actions Secrets..."
echo ""

# Database secrets
echo "Setting up database secrets..."
gh secret set DATABASE_URL --repo "$REPO_NAME" --body "postgresql://laas_user:SecurePassword123!@/laas_db?host=/cloudsql/laas-platform-1758016737:us-central1:laas-sql"

# Redis secrets (if needed)
echo "Setting up Redis secrets..."
gh secret set REDIS_URL --repo "$REPO_NAME" --body "redis://10.0.0.3:6379"

# JWT secrets
echo "Setting up JWT secrets..."
gh secret set JWT_SECRET_KEY --repo "$REPO_NAME" --body "your-super-secret-jwt-key-change-this-in-production"
gh secret set JWT_ALGORITHM --repo "$REPO_NAME" --body "HS256"

# Google Cloud secrets
echo "Setting up Google Cloud secrets..."
gh secret set GCP_PROJECT_ID --repo "$REPO_NAME" --body "laas-platform-1758016737"
gh secret set GCP_REGION --repo "$REPO_NAME" --body "us-central1"
gh secret set GCP_SERVICE_ACCOUNT_KEY --repo "$REPO_NAME" --body "$(cat service-account-key.json)"

# Cloud SQL connection name
echo "Setting up Cloud SQL connection..."
gh secret set CLOUDSQL_CONNECTION_NAME --repo "$REPO_NAME" --body "laas-platform-1758016737:us-central1:laas-sql"

# Artifact Registry
echo "Setting up Artifact Registry..."
gh secret set ARTIFACT_REGISTRY_REPOSITORY --repo "$REPO_NAME" --body "laas"
gh secret set ARTIFACT_REGISTRY_LOCATION --repo "$REPO_NAME" --body "us-central1"

# Environment
echo "Setting up environment..."
gh secret set ENVIRONMENT --repo "$REPO_NAME" --body "production"

echo ""
echo "✅ All GitHub Actions secrets have been set!"
echo ""
echo "📋 Summary of secrets created:"
echo "  - DATABASE_URL"
echo "  - REDIS_URL"
echo "  - JWT_SECRET_KEY"
echo "  - JWT_ALGORITHM"
echo "  - GCP_PROJECT_ID"
echo "  - GCP_REGION"
echo "  - GCP_SERVICE_ACCOUNT_KEY"
echo "  - CLOUDSQL_CONNECTION_NAME"
echo "  - ARTIFACT_REGISTRY_REPOSITORY"
echo "  - ARTIFACT_REGISTRY_LOCATION"
echo "  - ENVIRONMENT"
echo ""
echo "🚀 Your GitHub Actions workflows are now ready to deploy!"
echo ""
echo "Next steps:"
echo "1. Push your code to GitHub"
echo "2. GitHub Actions will automatically trigger on push to main"
echo "3. Monitor the deployment in the Actions tab"
echo ""
echo "🔍 To view your secrets, run:"
echo "   gh secret list --repo $REPO_NAME"