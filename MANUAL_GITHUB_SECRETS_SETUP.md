# 🔐 Manual GitHub Actions Secrets Setup

Since GitHub CLI authentication was interrupted, here's how to manually set up the required secrets in your GitHub repository.

## 📋 Required Secrets

You need to add these secrets to your GitHub repository:

### 1. Database Secrets
- **Name**: `DATABASE_URL`
- **Value**: `postgresql://laas_user:SecurePassword123!@/laas_db?host=/cloudsql/laas-platform-1758016737:us-central1:laas-sql`

### 2. Redis Secrets
- **Name**: `REDIS_URL`
- **Value**: `redis://10.0.0.3:6379`

### 3. JWT Secrets
- **Name**: `JWT_SECRET_KEY`
- **Value**: `your-super-secret-jwt-key-change-this-in-production`
- **Name**: `JWT_ALGORITHM`
- **Value**: `HS256`

### 4. Google Cloud Secrets
- **Name**: `GCP_PROJECT_ID`
- **Value**: `laas-platform-1758016737`
- **Name**: `GCP_REGION`
- **Value**: `us-central1`
- **Name**: `GCP_SERVICE_ACCOUNT_KEY`
- **Value**: (Copy the entire contents of `service-account-key.json`)

### 5. Cloud SQL Connection
- **Name**: `CLOUDSQL_CONNECTION_NAME`
- **Value**: `laas-platform-1758016737:us-central1:laas-sql`

### 6. Artifact Registry
- **Name**: `ARTIFACT_REGISTRY_REPOSITORY`
- **Value**: `laas`
- **Name**: `ARTIFACT_REGISTRY_LOCATION`
- **Value**: `us-central1`

### 7. Environment
- **Name**: `ENVIRONMENT`
- **Value**: `production`

## 🚀 How to Add Secrets in GitHub

1. **Go to your GitHub repository**
2. **Click on "Settings" tab**
3. **Click on "Secrets and variables" → "Actions"**
4. **Click "New repository secret"**
5. **Add each secret with the name and value above**
6. **Click "Add secret"**

## 📝 Service Account Key

For the `GCP_SERVICE_ACCOUNT_KEY` secret, you need to copy the entire contents of your `service-account-key.json` file:

```bash
cat service-account-key.json
```

Copy the entire JSON output and paste it as the value for the `GCP_SERVICE_ACCOUNT_KEY` secret.

## ✅ Verification

After adding all secrets, you can verify they're set by:
1. Going to your repository Settings → Secrets and variables → Actions
2. You should see all the secrets listed

## 🚀 Next Steps

Once all secrets are added:
1. **Push your code to GitHub**
2. **GitHub Actions will automatically trigger on push to main**
3. **Monitor the deployment in the Actions tab**

## 🔍 Troubleshooting

If you encounter issues:
- Make sure all secret names match exactly (case-sensitive)
- Verify the service account key JSON is valid
- Check that your GitHub repository has Actions enabled
- Ensure your Google Cloud project has the required APIs enabled

## 📞 Support

If you need help with any of these steps, let me know and I can guide you through the process!
