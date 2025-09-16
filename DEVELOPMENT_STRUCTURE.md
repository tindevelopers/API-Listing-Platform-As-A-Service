# LAAS Platform - Development Project Structure

## 🏗️ **Recommended Development Organization**

### **Single Cursor Workspace (Monorepo Approach)**

```
laas-platform-dev/                    # Your Cursor workspace root
├── services/                         # All API services
│   ├── core-api/                    # Main LAAS Platform API
│   │   ├── laas/                    # Your existing FastAPI app
│   │   ├── Dockerfile               # Service-specific Dockerfile
│   │   ├── requirements.txt         # Service dependencies
│   │   └── cloudrun.yaml           # Service-specific Cloud Run config
│   │
│   ├── tenant-api/                  # Tenant-specific API template
│   │   ├── laas/                    # Shared LAAS code (symlink or copy)
│   │   ├── Dockerfile               # Tenant-specific Dockerfile
│   │   ├── requirements.txt         # Tenant dependencies
│   │   └── cloudrun-tenant.yaml    # Tenant Cloud Run config
│   │
│   └── frontend/                    # Control Panel Frontend
│       ├── src/                     # React/Next.js source
│       ├── public/                  # Static assets
│       ├── Dockerfile               # Frontend Dockerfile
│       ├── package.json             # Frontend dependencies
│       └── cloudrun-frontend.yaml  # Frontend Cloud Run config
│
├── shared/                          # Shared libraries and utilities
│   ├── models/                      # Database models
│   ├── schemas/                     # Pydantic schemas
│   ├── utils/                       # Common utilities
│   └── config/                      # Shared configuration
│
├── infrastructure/                  # Infrastructure as Code
│   ├── cloud-run/                  # Cloud Run configurations
│   │   ├── core-api.yaml
│   │   ├── tenant-template.yaml
│   │   └── frontend.yaml
│   ├── terraform/                  # Terraform configurations
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── scripts/                    # Deployment scripts
│       ├── deploy.sh
│       ├── deploy-core.sh
│       └── deploy-tenant.sh
│
├── docs/                           # Documentation
│   ├── api/                        # API documentation
│   ├── deployment/                 # Deployment guides
│   └── development/                # Development guides
│
├── tests/                          # Integration and E2E tests
│   ├── integration/                # Cross-service tests
│   ├── e2e/                        # End-to-end tests
│   └── performance/                # Performance tests
│
├── .github/                        # GitHub Actions workflows
│   └── workflows/
│       ├── deploy-core.yml
│       ├── deploy-tenant.yml
│       └── deploy-frontend.yml
│
├── docker-compose.yml              # Local development
├── docker-compose.prod.yml         # Production-like local testing
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
├── README.md                       # Main project documentation
└── pyproject.toml                  # Python project configuration
```

## 🎯 **Benefits of This Structure**

### **1. Unified Development Experience**
- Single Cursor workspace for all services
- Shared code and utilities
- Consistent development environment
- Easy cross-service debugging

### **2. Simplified CI/CD**
- Single repository for all services
- Shared GitHub Actions workflows
- Consistent deployment process
- Easy dependency management

### **3. Better Code Organization**
- Clear separation of concerns
- Shared libraries and utilities
- Consistent project structure
- Easy to navigate and maintain

### **4. Efficient Resource Usage**
- Shared development tools and configurations
- Single Docker registry for all services
- Shared infrastructure configurations
- Reduced duplication

## 🚀 **Migration Strategy**

### **Step 1: Reorganize Current Project**
```bash
# Create new structure
mkdir -p services/core-api
mkdir -p services/tenant-api
mkdir -p services/frontend
mkdir -p shared
mkdir -p infrastructure
mkdir -p docs
mkdir -p tests

# Move existing code
mv laas/ services/core-api/
mv cloudrun.yaml services/core-api/
mv Dockerfile services/core-api/
mv requirements.txt services/core-api/
```

### **Step 2: Create Shared Libraries**
```bash
# Extract shared code
cp -r services/core-api/laas/models shared/
cp -r services/core-api/laas/schemas shared/
cp -r services/core-api/laas/utils shared/
cp -r services/core-api/laas/config shared/
```

### **Step 3: Update Service Configurations**
```bash
# Update import paths in services
# Create service-specific Dockerfiles
# Update Cloud Run configurations
```

## 🔧 **Development Workflow**

### **Local Development**
```bash
# Start all services locally
docker-compose up

# Start specific service
docker-compose up core-api

# Run tests
pytest tests/

# Run integration tests
pytest tests/integration/
```

### **Service Development**
```bash
# Work on core API
cd services/core-api
# Make changes to laas/ directory

# Work on tenant API
cd services/tenant-api
# Make changes to tenant-specific code

# Work on frontend
cd services/frontend
npm run dev
```

### **Deployment**
```bash
# Deploy all services
./infrastructure/scripts/deploy.sh all

# Deploy specific service
./infrastructure/scripts/deploy.sh core-api

# Deploy tenant service
./infrastructure/scripts/deploy.sh tenant-api TENANT_ID=tenant-123
```

## 📊 **Google Cloud Project Organization**

### **Development Environment**
```
Google Cloud Project: laas-platform-dev
├── Cloud Run Services:
│   ├── laas-core-api-dev
│   ├── laas-frontend-dev
│   └── laas-tenant-api-dev-{tenant-id}
├── Shared Infrastructure:
│   ├── Cloud SQL (dev database)
│   ├── Redis (dev cache)
│   └── Cloud Storage (dev files)
```

### **Production Environment**
```
Google Cloud Project: laas-platform-prod
├── Cloud Run Services:
│   ├── laas-core-api-prod
│   ├── laas-frontend-prod
│   └── laas-tenant-api-prod-{tenant-id}
├── Shared Infrastructure:
│   ├── Cloud SQL (prod database)
│   ├── Redis (prod cache)
│   └── Cloud Storage (prod files)
```

## 🎯 **Best Practices**

### **1. Code Organization**
- Keep shared code in `shared/` directory
- Use relative imports for shared modules
- Maintain consistent project structure
- Document service boundaries clearly

### **2. Development Workflow**
- Use feature branches for development
- Test locally with docker-compose
- Run integration tests before deployment
- Use consistent naming conventions

### **3. Deployment Strategy**
- Deploy services independently
- Use environment-specific configurations
- Implement proper health checks
- Monitor deployment success

### **4. Testing Strategy**
- Unit tests for each service
- Integration tests across services
- End-to-end tests for critical paths
- Performance tests for scalability

## 🔄 **Migration Commands**

### **Create New Structure**
```bash
# Create directory structure
mkdir -p services/{core-api,tenant-api,frontend}
mkdir -p shared/{models,schemas,utils,config}
mkdir -p infrastructure/{cloud-run,terraform,scripts}
mkdir -p docs/{api,deployment,development}
mkdir -p tests/{integration,e2e,performance}

# Move existing files
mv laas/ services/core-api/
mv cloudrun.yaml services/core-api/
mv Dockerfile services/core-api/
mv requirements.txt services/core-api/
mv deploy.sh infrastructure/scripts/
```

### **Update Import Paths**
```bash
# Update imports in core-api
find services/core-api -name "*.py" -exec sed -i 's/from laas/from shared/g' {} \;

# Create symlinks for shared code
ln -s ../../shared services/core-api/shared
ln -s ../../shared services/tenant-api/shared
```

### **Update Dockerfiles**
```bash
# Create service-specific Dockerfiles
cp services/core-api/Dockerfile services/tenant-api/
cp services/core-api/Dockerfile services/frontend/
```

## 📈 **Scaling Considerations**

### **As You Add More Services**
- Keep shared code in `shared/` directory
- Use consistent project structure
- Implement proper service discovery
- Maintain clear service boundaries

### **As You Add More Tenants**
- Use tenant-specific configurations
- Implement proper tenant isolation
- Monitor tenant-specific metrics
- Scale tenant services independently

## 🎉 **Next Steps**

### **1. Immediate Actions**
1. Create the new directory structure
2. Move existing code to appropriate locations
3. Update import paths and configurations
4. Test the new structure locally

### **2. Development Setup**
1. Update docker-compose for local development
2. Create service-specific development scripts
3. Set up shared library imports
4. Configure IDE for monorepo structure

### **3. Deployment Updates**
1. Update deployment scripts for new structure
2. Configure GitHub Actions for monorepo
3. Test deployment with new structure
4. Update documentation

This structure provides the optimal balance of organization, maintainability, and scalability for your LAAS Platform development.
