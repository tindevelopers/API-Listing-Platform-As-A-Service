# Google Cloud Run Deployment Strategy for LAAS Platform

## 🏗️ **Recommended Architecture**

### **Single Project with Multiple Services (Recommended)**

```
Google Cloud Project: laas-platform-prod
├── Core Services
│   ├── laas-api-core (Main LAAS Platform API)
│   └── laas-frontend (Control Panel Frontend)
├── Tenant Services (Auto-scaled per tenant)
│   ├── laas-api-tenant-{tenant-id} (Tenant-specific instances)
│   └── laas-api-tenant-{tenant-id} (Additional tenant instances)
└── Shared Infrastructure
    ├── Cloud SQL (PostgreSQL) - Shared database
    ├── Redis - Shared caching
    ├── Cloud Storage - Shared file storage
    └── Secret Manager - Shared secrets
```

## 🎯 **Why Single Project Architecture?**

### **Advantages:**
1. **Cost Efficiency**: Shared infrastructure reduces costs by 60-80%
2. **Simplified Management**: Single project to manage and monitor
3. **Resource Sharing**: Database, Redis, and storage can be shared across tenants
4. **Easier Monitoring**: Centralized logging, monitoring, and alerting
5. **Simplified Security**: Single IAM configuration and security policies
6. **Faster Deployment**: Shared CI/CD pipeline and deployment process

### **Multi-Tenant Isolation:**
- **Database Level**: Row Level Security (RLS) ensures tenant data isolation
- **Application Level**: Tenant middleware validates and routes requests
- **Network Level**: Each service has its own URL and can be configured with custom domains

## 🚀 **Deployment Configuration**

### **1. Core API Service (laas-api-core)**
```yaml
# Purpose: Main LAAS Platform API for management and multi-tenant operations
# Resources: 2 CPU, 2GB RAM (higher resources for management operations)
# Scaling: 0-100 instances
# URL: https://laas-api-core-{project-id}.{region}.run.app
```

### **2. Frontend Control Panel (laas-frontend)**
```yaml
# Purpose: React/Next.js frontend for platform management
# Resources: 1 CPU, 1GB RAM (optimized for frontend)
# Scaling: 0-50 instances
# URL: https://laas-frontend-{project-id}.{region}.run.app
```

### **3. Tenant API Services (laas-api-tenant-{tenant-id})**
```yaml
# Purpose: Tenant-specific API instances for dedicated performance
# Resources: 1 CPU, 1GB RAM (optimized for tenant workloads)
# Scaling: 0-20 instances per tenant
# URL: https://laas-api-tenant-{tenant-id}-{project-id}.{region}.run.app
```

## 📊 **Resource Allocation Strategy**

### **Shared Infrastructure:**
- **Cloud SQL**: Single PostgreSQL instance with connection pooling
- **Redis**: Single Redis instance with database separation (0-15 for different tenants)
- **Cloud Storage**: Single bucket with tenant-specific folders
- **Secret Manager**: Shared secrets with tenant-specific access controls

### **Service Scaling:**
- **Core API**: Higher resources for management operations
- **Frontend**: Optimized for web serving
- **Tenant APIs**: Auto-scaled based on individual tenant traffic

## 🔧 **Configuration Files**

### **1. Core API (cloudrun.yaml)**
- Main LAAS Platform API
- Higher resource allocation
- Full feature set enabled

### **2. Frontend (cloudrun-frontend.yaml)**
- React/Next.js application
- Optimized for web serving
- Environment variables for API endpoints

### **3. Tenant Template (cloudrun-tenant-template.yaml)**
- Template for tenant-specific deployments
- Tenant-specific environment variables
- Optimized resource allocation

## 🚀 **Deployment Process**

### **1. Initial Deployment**
```bash
# Deploy core infrastructure
./deploy.sh infra

# Deploy core API service
./deploy.sh deploy-core

# Deploy frontend (if available)
./deploy.sh deploy-frontend
```

### **2. Tenant Deployment**
```bash
# Deploy new tenant service
./deploy.sh deploy-tenant TENANT_ID=tenant-123

# Update existing tenant
./deploy.sh update-tenant TENANT_ID=tenant-123
```

### **3. Automated Deployment (GitHub Actions)**
```yaml
# Triggers on push to main branch
# Builds and deploys core services
# Can be configured to deploy tenant services based on changes
```

## 💰 **Cost Optimization**

### **Development Environment:**
- **Cloud SQL**: db-f1-micro (shared)
- **Redis**: Basic tier, 1GB
- **Cloud Run**: Min instances = 0 (pay per use)
- **Estimated Cost**: $50-100/month

### **Production Environment:**
- **Cloud SQL**: db-g1-small or higher (shared)
- **Redis**: Standard tier, 4GB
- **Cloud Run**: Min instances = 1 for core services
- **Estimated Cost**: $200-500/month (scales with usage)

### **Cost Benefits of Single Project:**
- **Shared Database**: 70% cost reduction vs separate databases
- **Shared Redis**: 80% cost reduction vs separate instances
- **Shared Storage**: 60% cost reduction vs separate buckets
- **Shared Monitoring**: 50% cost reduction vs separate monitoring

## 🔒 **Security & Isolation**

### **Multi-Tenant Security:**
1. **Database Level**: Row Level Security (RLS) ensures data isolation
2. **Application Level**: Tenant middleware validates requests
3. **Network Level**: Each service has isolated endpoints
4. **Access Control**: IAM roles and policies for service access

### **Tenant Isolation:**
- **Data**: RLS policies ensure tenant data separation
- **Compute**: Separate Cloud Run services per tenant
- **Network**: Custom domains and SSL certificates
- **Monitoring**: Tenant-specific metrics and logging

## 📈 **Scaling Strategy**

### **Horizontal Scaling:**
- **Core API**: 0-100 instances (auto-scaling)
- **Frontend**: 0-50 instances (auto-scaling)
- **Tenant APIs**: 0-20 instances per tenant (auto-scaling)

### **Vertical Scaling:**
- **Core API**: 2 CPU, 2GB RAM (management operations)
- **Frontend**: 1 CPU, 1GB RAM (web serving)
- **Tenant APIs**: 1 CPU, 1GB RAM (API operations)

### **Database Scaling:**
- **Connection Pooling**: Shared across all services
- **Read Replicas**: Can be added for read-heavy workloads
- **Partitioning**: By tenant for large-scale deployments

## 🔄 **CI/CD Pipeline**

### **GitHub Actions Workflow:**
1. **Build**: Docker images for core and tenant services
2. **Test**: Automated testing suite
3. **Deploy Core**: Deploy core API and frontend
4. **Deploy Tenants**: Deploy tenant services (if needed)
5. **Health Check**: Verify all services are healthy

### **Deployment Triggers:**
- **Core Changes**: Deploy core API and frontend
- **Tenant Changes**: Deploy specific tenant services
- **Infrastructure Changes**: Deploy all services

## 📊 **Monitoring & Observability**

### **Centralized Monitoring:**
- **Cloud Logging**: All services log to same project
- **Cloud Monitoring**: Unified metrics and dashboards
- **Error Reporting**: Centralized error tracking
- **Performance Monitoring**: Service-level metrics

### **Tenant-Specific Monitoring:**
- **Custom Metrics**: Per-tenant performance metrics
- **Log Filtering**: Tenant-specific log queries
- **Alerting**: Tenant-specific alerts and notifications

## 🎯 **Best Practices**

### **1. Resource Management:**
- Use shared infrastructure where possible
- Implement proper connection pooling
- Monitor resource usage and optimize

### **2. Security:**
- Implement proper IAM roles and policies
- Use Secret Manager for sensitive data
- Enable audit logging for all operations

### **3. Performance:**
- Use Redis for caching frequently accessed data
- Implement proper database indexing
- Monitor and optimize query performance

### **4. Cost Optimization:**
- Use min instances = 0 for development
- Monitor usage and adjust resources
- Implement proper auto-scaling policies

## 🚀 **Next Steps**

### **1. Immediate Actions:**
1. Set your `PROJECT_ID` environment variable
2. Run `./deploy.sh all` to deploy the core platform
3. Configure your domain and SSL certificates
4. Set up monitoring and alerting

### **2. Tenant Onboarding:**
1. Create tenant-specific Cloud Run services
2. Configure custom domains for tenants
3. Set up tenant-specific monitoring
4. Implement tenant management workflows

### **3. Scaling Considerations:**
1. Monitor resource usage and costs
2. Implement database read replicas if needed
3. Consider multi-region deployment for global tenants
4. Implement advanced caching strategies

## 📞 **Support & Maintenance**

### **Monitoring:**
- **Health Checks**: All services have health check endpoints
- **Logging**: Centralized logging in Cloud Logging
- **Metrics**: Performance metrics in Cloud Monitoring
- **Alerts**: Configurable alerts for key metrics

### **Maintenance:**
- **Updates**: Automated deployment via GitHub Actions
- **Backups**: Automated database backups
- **Scaling**: Automatic scaling based on demand
- **Security**: Regular security updates and patches

This architecture provides the optimal balance of cost efficiency, scalability, and maintainability for your LAAS Platform deployment on Google Cloud Run.
