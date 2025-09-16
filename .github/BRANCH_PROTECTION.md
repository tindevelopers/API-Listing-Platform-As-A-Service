# Branch Protection Setup

This document provides instructions for setting up branch protection rules and required status checks for the LAAS Platform repository.

## 🛡️ **Recommended Branch Protection Rules**

### **Main Branch (`main`)**

**Protection Settings**:
- ✅ Require a pull request before merging
- ✅ Require approvals: 2 reviewers
- ✅ Dismiss stale PR approvals when new commits are pushed
- ✅ Require review from code owners
- ✅ Restrict pushes that create files larger than 100MB
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ✅ Require conversation resolution before merging
- ✅ Include administrators
- ✅ Allow force pushes: ❌ (disabled)
- ✅ Allow deletions: ❌ (disabled)

**Required Status Checks**:
- `lint` - Code Quality & Linting
- `security` - Security Scan
- `test` - Unit Tests
- `build` - Build Docker Image
- `dependency-review` - Dependency Review
- `codeql` - CodeQL Analysis

### **Develop Branch (`develop`)**

**Protection Settings**:
- ✅ Require a pull request before merging
- ✅ Require approvals: 1 reviewer
- ✅ Dismiss stale PR approvals when new commits are pushed
- ✅ Require review from code owners
- ✅ Restrict pushes that create files larger than 100MB
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ✅ Require conversation resolution before merging
- ✅ Include administrators
- ✅ Allow force pushes: ❌ (disabled)
- ✅ Allow deletions: ❌ (disabled)

**Required Status Checks**:
- `lint` - Code Quality & Linting
- `security` - Security Scan
- `test` - Unit Tests
- `build` - Build Docker Image

## 🔧 **Setup Instructions**

### **1. Access Repository Settings**

1. Go to your GitHub repository
2. Click on **Settings** tab
3. Click on **Branches** in the left sidebar

### **2. Add Branch Protection Rule for Main**

1. Click **Add rule**
2. In **Branch name pattern**, enter: `main`
3. Configure the following settings:

**Protect matching branches**:
- ✅ Require a pull request before merging
- ✅ Require approvals: `2`
- ✅ Dismiss stale PR approvals when new commits are pushed
- ✅ Require review from code owners
- ✅ Restrict pushes that create files larger than: `100`
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ✅ Require conversation resolution before merging
- ✅ Include administrators

**Required status checks**:
- ✅ Require branches to be up to date before merging
- Add the following status checks:
  - `lint`
  - `security`
  - `test`
  - `build`
  - `dependency-review`
  - `codeql`

4. Click **Create**

### **3. Add Branch Protection Rule for Develop**

1. Click **Add rule**
2. In **Branch name pattern**, enter: `develop`
3. Configure the following settings:

**Protect matching branches**:
- ✅ Require a pull request before merging
- ✅ Require approvals: `1`
- ✅ Dismiss stale PR approvals when new commits are pushed
- ✅ Require review from code owners
- ✅ Restrict pushes that create files larger than: `100`
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ✅ Require conversation resolution before merging
- ✅ Include administrators

**Required status checks**:
- ✅ Require branches to be up to date before merging
- Add the following status checks:
  - `lint`
  - `security`
  - `test`
  - `build`

4. Click **Create**

## 👥 **Code Owners Setup**

Create a `.github/CODEOWNERS` file to define code ownership:

```bash
# Global code owners
* @your-username @team-lead-username

# Database and models
/laas/database/ @database-team
/laas/database/models.py @database-team @senior-developer

# API endpoints
/laas/api/ @api-team
/laas/api/v1/endpoints/ @api-team @senior-developer

# Authentication and security
/laas/auth/ @security-team @senior-developer

# Infrastructure and deployment
/.github/workflows/ @devops-team
/cloudrun.yaml @devops-team
/deploy.sh @devops-team

# Documentation
*.md @documentation-team
```

## 🔄 **Workflow Integration**

### **Required Status Checks**

The following status checks are automatically created by the GitHub Actions workflows:

| Check Name | Workflow | Purpose |
|------------|----------|---------|
| `lint` | `ci.yml` | Code quality and formatting |
| `security` | `ci.yml` | Security scanning |
| `test` | `ci.yml` | Unit tests and coverage |
| `build` | `ci.yml` | Docker image build |
| `dependency-review` | `ci.yml` | Dependency security review |
| `codeql` | `ci.yml` | Static code analysis |

### **Optional Status Checks**

These checks run but are not required for merging:

| Check Name | Workflow | Purpose |
|------------|----------|---------|
| `performance-test` | `deploy.yml` | Performance testing on staging |
| `security-scan` | `deploy.yml` | Container security scanning |

## 🚀 **Deployment Workflow Integration**

### **Environment Protection**

Set up environment protection rules:

1. Go to **Settings** → **Environments**
2. Create environments: `staging`, `production`

**Staging Environment**:
- ✅ Required reviewers: None (automatic deployment)
- ✅ Wait timer: 0 minutes
- ✅ Prevent self-review: ❌

**Production Environment**:
- ✅ Required reviewers: Add team leads
- ✅ Wait timer: 5 minutes
- ✅ Prevent self-review: ✅

### **Deployment Branches**

Configure which branches can deploy to each environment:

**Staging**:
- ✅ All branches
- ✅ Selected branches: `develop`

**Production**:
- ❌ All branches
- ✅ Selected branches: `main`
- ✅ Selected tags: `v*`

## 📊 **Status Check Monitoring**

### **Viewing Status Checks**

1. **Pull Request View**:
   - Status checks appear at the bottom of PRs
   - Green checkmark: Passed
   - Red X: Failed
   - Yellow circle: In progress

2. **Commit View**:
   - Click on commit SHA to see all status checks
   - View detailed logs for each check

3. **Branch View**:
   - Go to repository → Branches
   - See latest status for each branch

### **Troubleshooting Failed Checks**

1. **Lint Failures**:
   ```bash
   # Fix formatting issues
   black laas/
   isort laas/
   
   # Fix linting issues
   flake8 laas/
   ```

2. **Test Failures**:
   ```bash
   # Run tests locally
   ./run_tests.sh all
   
   # Run specific test
   pytest tests/test_database.py -v
   ```

3. **Security Failures**:
   ```bash
   # Check for vulnerabilities
   safety check
   
   # Fix security issues
   bandit -r laas/
   ```

4. **Build Failures**:
   ```bash
   # Test Docker build locally
   docker build -t laas-platform:test .
   ```

## 🔒 **Security Considerations**

### **Branch Protection Benefits**

- **Prevents direct pushes** to protected branches
- **Requires code review** before merging
- **Ensures quality gates** are passed
- **Maintains code history** integrity
- **Prevents force pushes** that could rewrite history

### **Additional Security Measures**

1. **Two-Factor Authentication**:
   - Require 2FA for all repository contributors
   - Go to Settings → Security → Two-factor authentication

2. **Branch Protection for All Branches**:
   - Consider protecting feature branches
   - Use patterns like `feature/*`, `bugfix/*`

3. **Automated Security Scanning**:
   - Dependabot for dependency updates
   - CodeQL for static analysis
   - Trivy for container scanning

## 📝 **Best Practices**

### **Pull Request Workflow**

1. **Create Feature Branch**:
   ```bash
   git checkout -b feature/new-functionality
   git push -u origin feature/new-functionality
   ```

2. **Create Pull Request**:
   - Target `develop` for new features
   - Target `main` for hotfixes
   - Include descriptive title and description
   - Link related issues

3. **Code Review Process**:
   - Request reviews from code owners
   - Address all review comments
   - Ensure all status checks pass
   - Resolve conversations

4. **Merge Strategy**:
   - Use "Squash and merge" for feature branches
   - Use "Merge commit" for release branches
   - Delete feature branches after merging

### **Release Process**

1. **Create Release Branch**:
   ```bash
   git checkout develop
   git checkout -b release/v1.0.0
   git push -u origin release/v1.0.0
   ```

2. **Merge to Main**:
   - Create PR from `release/v1.0.0` to `main`
   - Get required approvals
   - Merge to main

3. **Create Tag**:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

4. **Merge Back to Develop**:
   - Create PR from `main` to `develop`
   - Merge to keep develop up to date

## 🆘 **Troubleshooting**

### **Common Issues**

1. **Status Checks Not Appearing**:
   - Ensure workflows are in `.github/workflows/`
   - Check workflow syntax
   - Verify trigger conditions

2. **Required Checks Not Found**:
   - Wait for workflow to complete
   - Check workflow logs for errors
   - Verify job names match required checks

3. **Merge Button Disabled**:
   - Check all required status checks are passing
   - Ensure required reviews are completed
   - Verify branch is up to date

4. **Permission Denied**:
   - Check repository permissions
   - Verify branch protection settings
   - Ensure user has appropriate access

### **Emergency Override**

In case of emergency, repository administrators can:

1. **Temporarily Disable Protection**:
   - Go to Settings → Branches
   - Edit branch protection rule
   - Uncheck "Include administrators"
   - Make necessary changes
   - Re-enable protection

2. **Force Push** (if allowed):
   ```bash
   git push --force-with-lease origin main
   ```

3. **Direct Push** (if allowed):
   ```bash
   git push origin main
   ```

**⚠️ Warning**: Use emergency overrides sparingly and always re-enable protection afterward.

