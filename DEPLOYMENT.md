# LAAS Platform - Google Cloud Run Deployment Guide

This guide provides step-by-step instructions for deploying the LAAS Platform to Google Cloud Run.

## Prerequisites

### Required Tools
- [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) (gcloud)
- [Docker](https://docs.docker.com/get-docker/)
- [Git](https://git-scm.com/downloads)

### Google Cloud Requirements
- Google Cloud Project with billing enabled
- Owner or Editor role on the project
- Required APIs enabled (handled by deployment script)

## Quick Start

### 1. Set Environment Variables
```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"  # Optional, defaults to us-central1
```

### 2. Run Deployment Script
```bash
# Make script executable (if not already)
chmod +x deploy.sh

# Deploy everything
./deploy.sh all
```

## Manual Deployment Steps

If you prefer to run each step manually:

### 1. Check Dependencies
```bash
./deploy.sh check
```

### 2. Authenticate and Setup
```bash
./deploy.sh auth
```

### 3. Create Infrastructure
```bash
./deploy.sh infra
```

### 4. Create Secrets
```bash
./deploy.sh secrets
```

### 5. Build and Push Image
```bash
./deploy.sh build
```

### 6. Deploy to Cloud Run
```bash
./deploy.sh deploy
```

### 7. Run Database Migrations
```bash
./deploy.sh migrate
```

## Infrastructure Components

The deployment creates the following Google Cloud resources:

### Cloud Run Service
- **Name**: `laas-api`
- **Region**: Configurable (default: us-central1)
- **Resources**: 2 CPU, 2GB RAM
- **Scaling**: 0-100 instances
- **Concurrency**: 1000 requests per instance

### Cloud SQL (PostgreSQL)
- **Instance**: `laas-sql`
- **Version**: PostgreSQL 15
- **Tier**: db-f1-micro (can be upgraded)
- **Storage**: 10GB SSD
- **Features**: Automated backups, IP aliasing

### Redis
- **Instance**: `laas-redis`
- **Version**: Redis 7.0
- **Tier**: Basic
- **Size**: 1GB

### Artifact Registry
- **Repository**: `laas`
- **Format**: Docker
- **Location**: Same as Cloud Run region

### Secret Manager
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET_KEY`: JWT signing secret
- `SECRET_KEY`: Application secret key
- `REDIS_URL`: Redis connection string

## Configuration

### Environment Variables

The following environment variables are automatically configured:

| Variable | Source | Description |
|----------|--------|-------------|
| `ENVIRONMENT` | Cloud Run | Set to "production" |
| `DATABASE_URL` | Secret Manager | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Secret Manager | JWT signing secret |
| `SECRET_KEY` | Secret Manager | Application secret key |
| `REDIS_URL` | Secret Manager | Redis connection string |
| `GOOGLE_CLOUD_PROJECT_ID` | Cloud Run | Your project ID |
| `GOOGLE_CLOUD_REGION` | Cloud Run | Deployment region |
| `CORS_ORIGINS` | Cloud Run | Allowed CORS origins |
| `ALLOWED_HOSTS` | Cloud Run | Allowed hostnames |
| `LOG_LEVEL` | Cloud Run | Set to "INFO" |

### Custom Configuration

To customize the deployment:

1. **Update `cloudrun.yaml`** for Cloud Run configuration
2. **Modify `deploy.sh`** for infrastructure settings
3. **Update `env.production`** for application settings

## Database Setup

### Initial Schema
The deployment automatically:
1. Creates the database and user
2. Runs the initialization script (`database/init.sql`)
3. Creates all tables via SQLAlchemy models
4. Inserts default data (tenant, user, categories, tags)

### Default Credentials
- **Database**: `laas_platform`
- **User**: `laas_user`
- **Password**: Auto-generated and stored in Secret Manager

### Admin Access
Default admin user created:
- **Email**: `admin@laas-platform.com`
- **Password**: `admin123` (change immediately!)
- **Role**: `superadmin`

## Monitoring and Logging

### Health Checks
- **Endpoint**: `https://your-service-url/health`
- **Liveness Probe**: Every 10 seconds
- **Readiness Probe**: Every 5 seconds

### Logging
- **Format**: JSON structured logs
- **Level**: INFO (configurable)
- **Destination**: Google Cloud Logging

### Monitoring
- **Metrics**: Available in Google Cloud Monitoring
- **Alerts**: Can be configured for key metrics
- **Tracing**: Available with Cloud Trace

## Security

### Network Security
- **Ingress**: All (configurable)
- **Authentication**: JWT-based
- **HTTPS**: Enforced by Cloud Run
- **CORS**: Configured for your domains

### Data Security
- **Encryption**: At rest and in transit
- **Secrets**: Stored in Secret Manager
- **Database**: Private IP with Cloud SQL Proxy
- **Redis**: Private IP access only

## Scaling and Performance

### Auto-scaling
- **Min Instances**: 0 (cost optimization)
- **Max Instances**: 100 (configurable)
- **CPU Utilization**: 60% (default)
- **Request-based**: Scales with traffic

### Performance Optimization
- **Connection Pooling**: Configured for database
- **Redis Caching**: Available for session storage
- **CDN**: Can be added for static assets
- **Load Balancing**: Handled by Cloud Run

## Troubleshooting

### Common Issues

#### 1. Authentication Errors
```bash
# Re-authenticate
gcloud auth login
gcloud auth configure-docker
```

#### 2. Permission Errors
```bash
# Check project permissions
gcloud projects get-iam-policy $PROJECT_ID
```

#### 3. Database Connection Issues
```bash
# Check Cloud SQL instance
gcloud sql instances describe laas-sql
```

#### 4. Service Not Starting
```bash
# Check logs
gcloud run services logs read laas-api --region=$REGION
```

### Debug Commands

#### View Service Status
```bash
gcloud run services describe laas-api --region=$REGION
```

#### Check Database
```bash
gcloud sql connect laas-sql --user=laas_user --database=laas_platform
```

#### View Logs
```bash
gcloud run services logs read laas-api --region=$REGION --limit=100
```

## Cost Optimization

### Development Environment
- Use `db-f1-micro` for Cloud SQL
- Set `min-instances=0` for Cloud Run
- Use `basic` tier for Redis

### Production Environment
- Upgrade to `db-g1-small` or higher for Cloud SQL
- Consider `min-instances=1` for faster cold starts
- Monitor usage and adjust resources accordingly

## Backup and Recovery

### Database Backups
- **Automated**: Daily backups (7-day retention)
- **Manual**: Can be created via Cloud Console
- **Point-in-time**: Available for recovery

### Application Data
- **Media Files**: Store in Cloud Storage
- **Configuration**: Version controlled in Git
- **Secrets**: Backed up in Secret Manager

## Updates and Maintenance

### Application Updates
```bash
# Build and deploy new version
./deploy.sh build
./deploy.sh deploy
```

### Database Migrations
```bash
# Run migrations
./deploy.sh migrate
```

### Infrastructure Updates
- Update `cloudrun.yaml` for Cloud Run changes
- Modify `deploy.sh` for infrastructure changes
- Re-run deployment steps as needed

## Support

### Documentation
- **API Docs**: Available at `/docs` endpoint
- **Health Check**: Available at `/health` endpoint
- **OpenAPI Spec**: Available at `/openapi.json`

### Monitoring
- **Google Cloud Console**: Monitor resources
- **Cloud Logging**: View application logs
- **Cloud Monitoring**: Set up alerts

### Contact
For issues or questions:
1. Check the logs first
2. Review this documentation
3. Check Google Cloud status
4. Contact your system administrator

