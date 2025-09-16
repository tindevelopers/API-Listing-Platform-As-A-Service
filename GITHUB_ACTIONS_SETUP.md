# GitHub Actions Setup for LAAS Platform

This document explains how to set up and use the GitHub Actions workflows for automated deployment of the LAAS platform to Google Cloud Run.

## Workflows Overview

### 1. Main Deployment Workflow (`.github/workflows/deploy.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` branch

**Jobs:**
1. **Test** - Runs tests, linting, and code quality checks
2. **Build and Deploy** - Builds Docker image and deploys to Cloud Run
3. **Security Scan** - Runs vulnerability scanning (main branch only)

### 2. Database Migration Workflow (`.github/workflows/migrate.yml`)

**Triggers:**
- Manual workflow dispatch

**Actions:**
- `upgrade` - Run database migrations forward
- `downgrade` - Rollback to specific revision
- `reset` - Reset database and run all migrations

### 3. Secrets Management Workflow (`.github/workflows/secrets.yml`)

**Triggers:**
- Manual workflow dispatch

**Actions:**
- `list` - Show all secrets in Google Cloud Secret Manager
- `create` - Create new secret
- `update` - Update existing secret
- `delete` - Delete secret

## Setup Requirements

### 1. GitHub Repository Secrets

Configure these secrets in your GitHub repository settings:

```
GCP_SA_KEY          # Service account JSON key for authentication
DB_PASSWORD         # Database password for migrations
```

### 2. Service Account Permissions

The service account needs these roles:
- Cloud Run Admin
- Cloud Build Editor
- Secret Manager Secret Accessor
- Artifact Registry Writer
- Cloud SQL Client

## Setup Steps

### Step 1: Add GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following secrets:

#### GCP_SA_KEY
```bash
# Copy the service account key we created earlier
cat service-account-key.json
```
Paste the entire JSON content as the secret value.

#### DB_PASSWORD
```bash
# Get the database password from Google Cloud
gcloud sql users describe laas_user --instance=laas-sql
```
Use the password value as the secret.

### Step 2: Verify Google Cloud Setup

Ensure these resources exist in your Google Cloud project:
- Cloud SQL instance: `laas-sql`
- Artifact Registry repository: `laas`
- Secret Manager secrets: `DATABASE_URL`, `JWT_SECRET_KEY`, `SECRET_KEY`, `REDIS_URL`

### Step 3: Test the Workflow

1. **Push to main branch** to trigger automatic deployment
2. **Create a pull request** to test the CI pipeline
3. **Check Actions tab** to monitor workflow execution

## Workflow Details

### Deployment Process

1. **Code Quality Checks**
   - Python linting with flake8
   - Code formatting with black
   - Import sorting with isort
   - Unit tests with pytest

2. **Docker Build**
   - Multi-stage build for production
   - Push to Artifact Registry
   - Tag with commit SHA

3. **Cloud Run Deployment**
   - Deploy with proper resource allocation
   - Configure environment variables
   - Set up health checks
   - Connect to Cloud SQL

4. **Health Verification**
   - Wait for service readiness
   - Run health check endpoint
   - Report deployment status

### Environment Configuration

**Production Environment Variables:**
- `ENVIRONMENT=production`
- `GOOGLE_CLOUD_PROJECT_ID=laas-platform-1758016737`
- `GOOGLE_CLOUD_REGION=us-central1`

**Secrets from Secret Manager:**
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - JWT signing secret
- `SECRET_KEY` - Application secret key
- `REDIS_URL` - Redis connection string

### Resource Allocation

**Cloud Run Configuration:**
- **Memory**: 2Gi
- **CPU**: 2 cores
- **Port**: 8000
- **Min Instances**: 0 (cost optimization)
- **Max Instances**: 100
- **Concurrency**: 1000 requests per instance
- **Timeout**: 300 seconds

## Manual Workflows

### Database Migration

1. Go to **Actions** tab in GitHub
2. Select **Database Migration** workflow
3. Click **Run workflow**
4. Choose migration type:
   - **upgrade**: Apply new migrations
   - **downgrade**: Rollback to specific revision
   - **reset**: Reset and reapply all migrations

### Secrets Management

1. Go to **Actions** tab in GitHub
2. Select **Manage Secrets** workflow
3. Click **Run workflow**
4. Choose action:
   - **list**: View all secrets
   - **create**: Add new secret
   - **update**: Modify existing secret
   - **delete**: Remove secret

## Monitoring and Troubleshooting

### Workflow Status

Monitor workflow execution in:
- **GitHub Actions tab** - Real-time execution status
- **Cloud Build console** - Build logs and details
- **Cloud Run console** - Deployment status and logs

### Common Issues

1. **Authentication Failures**
   - Verify `GCP_SA_KEY` secret is correctly formatted
   - Check service account permissions

2. **Build Failures**
   - Review Docker build logs
   - Check dependency installation

3. **Deployment Failures**
   - Verify Cloud Run configuration
   - Check environment variables and secrets

4. **Health Check Failures**
   - Review application logs
   - Verify database connectivity

### Logs and Debugging

**GitHub Actions Logs:**
- Available in the Actions tab
- Download logs for detailed debugging

**Cloud Run Logs:**
```bash
gcloud run services logs read laas-api --region=us-central1 --limit=100
```

**Cloud Build Logs:**
```bash
gcloud builds log [BUILD_ID] --region=us-central1
```

## Security Considerations

### Secret Management
- All sensitive data stored in Google Secret Manager
- GitHub secrets used only for authentication
- No hardcoded credentials in workflow files

### Access Control
- Service account with minimal required permissions
- Workflows run in isolated environments
- No access to other Google Cloud projects

### Vulnerability Scanning
- Automated security scanning with Trivy
- Results uploaded to GitHub Security tab
- Regular dependency updates

## Cost Optimization

### Resource Management
- Min instances set to 0 for cost savings
- Automatic scaling based on demand
- Efficient Docker image building

### Monitoring
- Set up billing alerts
- Monitor resource usage
- Optimize based on actual usage patterns

## Support and Maintenance

### Regular Tasks
- Update dependencies monthly
- Review security scan results
- Monitor deployment performance

### Backup Strategy
- Database automated backups
- Configuration version control
- Deployment rollback capability

For issues or questions:
1. Check GitHub Actions logs
2. Review Cloud Run deployment status
3. Verify Google Cloud resource configuration
4. Contact system administrator