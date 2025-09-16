# GitHub Actions Workflows

This directory contains GitHub Actions workflows for the LAAS Platform, providing automated CI/CD, testing, security scanning, and infrastructure management.

## 🔄 **Workflows Overview**

### 1. **Continuous Integration (`ci.yml`)**
- **Triggers**: Push to `main`/`develop`, Pull Requests
- **Purpose**: Code quality, security scanning, and testing
- **Jobs**:
  - **Lint**: Code formatting (Black), import sorting (isort), linting (Flake8), type checking (MyPy)
  - **Security**: Dependency vulnerability scanning (Safety), security linting (Bandit)
  - **Test**: Unit tests with coverage reporting
  - **Build**: Docker image build and validation
  - **Dependency Review**: Security review of dependencies
  - **CodeQL**: Static code analysis

### 2. **Deployment (`deploy.yml`)**
- **Triggers**: Push to `main`/`develop`, tags, manual dispatch
- **Purpose**: Automated deployment to Google Cloud Run
- **Environments**:
  - **Staging**: Deploys from `develop` branch
  - **Production**: Deploys from `main` branch or tags
- **Features**:
  - Automated testing before deployment
  - Docker image building and pushing
  - Cloud Run deployment with health checks
  - Performance testing on staging
  - Security scanning with Trivy
  - GitHub releases for tagged versions

### 3. **Infrastructure Management (`infrastructure.yml`)**
- **Triggers**: Manual dispatch only
- **Purpose**: Manage Google Cloud infrastructure
- **Actions**:
  - **Plan**: List existing infrastructure resources
  - **Apply**: Create/update infrastructure components
  - **Destroy**: Remove all infrastructure (use with caution)
- **Components**:
  - Cloud SQL (PostgreSQL)
  - Redis (Memorystore)
  - Artifact Registry
  - Secret Manager
  - Cloud Run services

### 4. **Database Migration (`migrate.yml`)**
- **Triggers**: Manual dispatch only
- **Purpose**: Database schema and data migrations
- **Migration Types**:
  - **Schema**: Create/update database tables
  - **Data**: Insert initial data and configurations
  - **Rollback**: Remove all tables (destructive)

## 🚀 **Getting Started**

### **Prerequisites**

1. **Google Cloud Project Setup**:
   ```bash
   # Create a new project or use existing one
   gcloud projects create your-project-id
   gcloud config set project your-project-id
   
   # Enable billing
   gcloud billing accounts list
   gcloud billing projects link your-project-id --billing-account=BILLING_ACCOUNT_ID
   ```

2. **Service Account Setup**:
   ```bash
   # Create service account
   gcloud iam service-accounts create github-actions \
     --display-name="GitHub Actions" \
     --description="Service account for GitHub Actions"
   
   # Grant necessary permissions
   gcloud projects add-iam-policy-binding your-project-id \
     --member="serviceAccount:github-actions@your-project-id.iam.gserviceaccount.com" \
     --role="roles/run.admin"
   
   gcloud projects add-iam-policy-binding your-project-id \
     --member="serviceAccount:github-actions@your-project-id.iam.gserviceaccount.com" \
     --role="roles/cloudsql.admin"
   
   gcloud projects add-iam-policy-binding your-project-id \
     --member="serviceAccount:github-actions@your-project-id.iam.gserviceaccount.com" \
     --role="roles/secretmanager.admin"
   
   gcloud projects add-iam-policy-binding your-project-id \
     --member="serviceAccount:github-actions@your-project-id.iam.gserviceaccount.com" \
     --role="roles/artifactregistry.admin"
   
   gcloud projects add-iam-policy-binding your-project-id \
     --member="serviceAccount:github-actions@your-project-id.iam.gserviceaccount.com" \
     --role="roles/redis.admin"
   
   # Create and download key
   gcloud iam service-accounts keys create github-actions-key.json \
     --iam-account=github-actions@your-project-id.iam.gserviceaccount.com
   ```

3. **GitHub Secrets Configuration**:
   Add the following secrets to your GitHub repository:
   - `GCP_PROJECT_ID`: Your Google Cloud project ID
   - `GCP_SA_KEY`: Contents of the service account key JSON file

### **Initial Setup**

1. **Create Infrastructure**:
   - Go to GitHub Actions tab
   - Run "Infrastructure Management" workflow
   - Select "apply" action and "staging" environment
   - Wait for completion

2. **Run Initial Migration**:
   - Run "Database Migration" workflow
   - Select "schema" migration type and "staging" environment
   - Then run "data" migration type

3. **Deploy to Staging**:
   - Push to `develop` branch or manually trigger deployment
   - Monitor the deployment in GitHub Actions

## 📋 **Workflow Usage**

### **Continuous Integration**

**Automatic Triggers**:
- Runs on every push to `main` or `develop`
- Runs on every pull request
- No manual intervention required

**Manual Triggers**:
```bash
# Push to trigger CI
git push origin develop

# Create pull request to trigger CI
gh pr create --title "Feature: Add new functionality"
```

### **Deployment**

**Automatic Deployment**:
- **Staging**: Deploys automatically when pushing to `develop`
- **Production**: Deploys automatically when pushing to `main` or creating tags

**Manual Deployment**:
1. Go to GitHub Actions → "Deploy to Google Cloud Run"
2. Click "Run workflow"
3. Select environment (staging/production)
4. Click "Run workflow"

**Tagged Releases**:
```bash
# Create and push a tag for production release
git tag v1.0.0
git push origin v1.0.0
```

### **Infrastructure Management**

**Plan Infrastructure**:
1. Go to GitHub Actions → "Infrastructure Management"
2. Select "plan" action
3. Choose environment
4. Review the output to see current resources

**Apply Infrastructure**:
1. Go to GitHub Actions → "Infrastructure Management"
2. Select "apply" action
3. Choose environment
4. Monitor the creation process

**Destroy Infrastructure** (⚠️ **DESTRUCTIVE**):
1. Go to GitHub Actions → "Infrastructure Management"
2. Select "destroy" action
3. Choose environment
4. Confirm the destruction

### **Database Migration**

**Schema Migration**:
1. Go to GitHub Actions → "Database Migration"
2. Select "schema" migration type
3. Choose environment
4. Monitor the migration process

**Data Migration**:
1. Go to GitHub Actions → "Database Migration"
2. Select "data" migration type
3. Choose environment
4. Monitor the data insertion

**Rollback** (⚠️ **DESTRUCTIVE**):
1. Go to GitHub Actions → "Database Migration"
2. Select "rollback" migration type
3. Choose environment
4. Confirm the rollback

## 🔧 **Configuration**

### **Environment Variables**

The workflows use the following environment variables:

| Variable | Description | Source |
|----------|-------------|---------|
| `PROJECT_ID` | Google Cloud project ID | GitHub Secret |
| `REGION` | Google Cloud region | Workflow default |
| `SERVICE_NAME` | Cloud Run service name | Workflow default |
| `REPOSITORY` | Artifact Registry repository | Workflow default |

### **Secrets Management**

Required GitHub Secrets:

| Secret | Description | How to Get |
|--------|-------------|------------|
| `GCP_PROJECT_ID` | Google Cloud project ID | From Google Cloud Console |
| `GCP_SA_KEY` | Service account key JSON | Generated during setup |

### **Environment Protection**

- **Production Environment**: Requires manual approval
- **Staging Environment**: Automatic deployment
- **Infrastructure Changes**: Manual dispatch only
- **Database Migrations**: Manual dispatch only

## 📊 **Monitoring & Notifications**

### **Workflow Status**

- **Green Checkmark**: All checks passed
- **Red X**: One or more checks failed
- **Yellow Circle**: Workflow in progress
- **Gray Circle**: Workflow cancelled

### **Notifications**

- **Pull Request Comments**: Staging deployment URLs
- **GitHub Releases**: Production deployment information
- **Workflow Artifacts**: Test reports, coverage, security scans

### **Logs and Debugging**

1. **View Workflow Logs**:
   - Go to GitHub Actions tab
   - Click on the workflow run
   - Expand individual job steps

2. **Download Artifacts**:
   - Test reports
   - Coverage reports
   - Security scan results
   - Performance reports

## 🛠️ **Troubleshooting**

### **Common Issues**

1. **Permission Denied**:
   - Check service account permissions
   - Verify GitHub secrets are set correctly
   - Ensure billing is enabled on the project

2. **Build Failures**:
   - Check Python dependencies in `requirements.txt`
   - Verify Docker build context
   - Review test failures in logs

3. **Deployment Failures**:
   - Check Cloud Run service limits
   - Verify secret references
   - Review health check endpoints

4. **Database Connection Issues**:
   - Verify Cloud SQL instance is running
   - Check database credentials in secrets
   - Ensure proper network configuration

### **Debug Commands**

```bash
# Check service account permissions
gcloud projects get-iam-policy your-project-id

# List Cloud Run services
gcloud run services list --region=us-central1

# Check Cloud SQL instances
gcloud sql instances list

# View secret versions
gcloud secrets versions list DATABASE_URL
```

## 🔒 **Security Best Practices**

1. **Service Account**:
   - Use least privilege principle
   - Rotate keys regularly
   - Monitor usage

2. **Secrets**:
   - Never commit secrets to code
   - Use GitHub Secrets for sensitive data
   - Rotate secrets periodically

3. **Infrastructure**:
   - Enable audit logging
   - Use private networks where possible
   - Regular security updates

4. **Code**:
   - Regular dependency updates
   - Security scanning in CI
   - Code review requirements

## 📚 **Additional Resources**

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)

## 🆘 **Support**

For issues with the workflows:

1. Check the workflow logs for error details
2. Verify all prerequisites are met
3. Review the troubleshooting section
4. Create an issue in the repository with:
   - Workflow name and run ID
   - Error messages
   - Steps to reproduce
   - Environment details

