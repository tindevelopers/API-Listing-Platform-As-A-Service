#!/bin/bash

# LAAS Platform - Migration to Monorepo Structure
# This script reorganizes your current project into a monorepo structure

set -e

echo "🚀 Starting LAAS Platform migration to monorepo structure..."

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p services/{core-api,tenant-api,frontend}
mkdir -p shared/{models,schemas,utils,config}
mkdir -p infrastructure/{cloud-run,terraform,scripts}
mkdir -p docs/{api,deployment,development}
mkdir -p tests/{integration,e2e,performance}
mkdir -p .github/workflows

# Move existing files to core-api
echo "📦 Moving existing files to core-api service..."
if [ -d "laas" ]; then
    mv laas services/core-api/
    echo "✅ Moved laas/ to services/core-api/"
fi

if [ -f "cloudrun.yaml" ]; then
    mv cloudrun.yaml services/core-api/
    echo "✅ Moved cloudrun.yaml to services/core-api/"
fi

if [ -f "Dockerfile" ]; then
    mv Dockerfile services/core-api/
    echo "✅ Moved Dockerfile to services/core-api/"
fi

if [ -f "requirements.txt" ]; then
    mv requirements.txt services/core-api/
    echo "✅ Moved requirements.txt to services/core-api/"
fi

# Move infrastructure files
echo "🏗️ Moving infrastructure files..."
if [ -f "cloudbuild.yaml" ]; then
    mv cloudbuild.yaml infrastructure/cloud-run/
    echo "✅ Moved cloudbuild.yaml to infrastructure/cloud-run/"
fi

if [ -f "deploy.sh" ]; then
    mv deploy.sh infrastructure/scripts/
    echo "✅ Moved deploy.sh to infrastructure/scripts/"
fi

if [ -f "docker-compose.yml" ]; then
    mv docker-compose.yml .
    echo "✅ Kept docker-compose.yml in root"
fi

# Move documentation
echo "📚 Moving documentation..."
if [ -f "PROJECT_SUMMARY.md" ]; then
    mv PROJECT_SUMMARY.md docs/
    echo "✅ Moved PROJECT_SUMMARY.md to docs/"
fi

if [ -f "DEPLOYMENT.md" ]; then
    mv DEPLOYMENT.md docs/deployment/
    echo "✅ Moved DEPLOYMENT.md to docs/deployment/"
fi

if [ -f "CLOUD_RUN_STRATEGY.md" ]; then
    mv CLOUD_RUN_STRATEGY.md docs/deployment/
    echo "✅ Moved CLOUD_RUN_STRATEGY.md to docs/deployment/"
fi

if [ -f "DEVELOPMENT_STRUCTURE.md" ]; then
    mv DEVELOPMENT_STRUCTURE.md docs/development/
    echo "✅ Moved DEVELOPMENT_STRUCTURE.md to docs/development/"
fi

# Move tests
echo "🧪 Moving tests..."
if [ -d "tests" ]; then
    mv tests/* tests/integration/ 2>/dev/null || true
    echo "✅ Moved existing tests to tests/integration/"
fi

# Create shared library structure
echo "📚 Creating shared library structure..."
if [ -d "services/core-api/laas" ]; then
    # Extract shared models
    if [ -d "services/core-api/laas/database/models.py" ]; then
        mkdir -p shared/models
        cp services/core-api/laas/database/models.py shared/models/
        echo "✅ Extracted models to shared/models/"
    fi
    
    # Extract shared schemas
    if [ -d "services/core-api/laas/schemas" ]; then
        cp -r services/core-api/laas/schemas/* shared/schemas/ 2>/dev/null || true
        echo "✅ Extracted schemas to shared/schemas/"
    fi
    
    # Extract shared config
    if [ -d "services/core-api/laas/core" ]; then
        cp -r services/core-api/laas/core/* shared/config/ 2>/dev/null || true
        echo "✅ Extracted config to shared/config/"
    fi
fi

# Create tenant-api structure
echo "🏢 Creating tenant-api structure..."
cp -r services/core-api/laas services/tenant-api/ 2>/dev/null || true
cp services/core-api/Dockerfile services/tenant-api/ 2>/dev/null || true
cp services/core-api/requirements.txt services/tenant-api/ 2>/dev/null || true

# Create tenant-specific Cloud Run config
cat > services/tenant-api/cloudrun-tenant.yaml << 'EOF'
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: laas-api-tenant-$(TENANT_ID)
  namespace: default
  annotations:
    run.googleapis.com/ingress: all
    run.googleapis.com/ingress-status: all
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/cpu-throttling: "false"
        run.googleapis.com/cloudsql-instances: "$(PROJECT_ID):$(REGION):laas-sql"
        autoscaling.knative.dev/minScale: "0"
        autoscaling.knative.dev/maxScale: "20"
        run.googleapis.com/execution-environment: gen2
    spec:
      containerConcurrency: 500
      timeoutSeconds: 300
      containers:
        - image: $(REGION)-docker.pkg.dev/$(PROJECT_ID)/laas/laas-api-tenant:$(REVISION)
          ports:
            - containerPort: 8000
          env:
            - name: ENVIRONMENT
              value: production
            - name: TENANT_ID
              value: $(TENANT_ID)
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: laas-secrets
                  key: DATABASE_URL
            - name: JWT_SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: laas-secrets
                  key: JWT_SECRET_KEY
            - name: SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: laas-secrets
                  key: SECRET_KEY
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: laas-secrets
                  key: REDIS_URL
            - name: GOOGLE_CLOUD_PROJECT_ID
              value: $(PROJECT_ID)
            - name: GOOGLE_CLOUD_REGION
              value: $(REGION)
            - name: CORS_ORIGINS
              value: "https://$(TENANT_ID).laas-platform.com,https://laas-frontend-$(PROJECT_ID).$(REGION).run.app"
            - name: ALLOWED_HOSTS
              value: "$(TENANT_ID).laas-platform.com,laas-api-tenant-$(TENANT_ID)-$(PROJECT_ID).$(REGION).run.app"
            - name: LOG_LEVEL
              value: "INFO"
          resources:
            limits:
              cpu: "1"
              memory: 1Gi
            requests:
              cpu: "0.5"
              memory: 512Mi
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
EOF

echo "✅ Created tenant-api structure"

# Create frontend structure
echo "🎨 Creating frontend structure..."
mkdir -p services/frontend/src
mkdir -p services/frontend/public

# Create basic frontend files
cat > services/frontend/package.json << 'EOF'
{
  "name": "laas-frontend",
  "version": "1.0.0",
  "description": "LAAS Platform Control Panel",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.0",
    "typescript": "^5.0.0"
  }
}
EOF

cat > services/frontend/Dockerfile << 'EOF'
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Install dependencies based on the preferred package manager
COPY package.json package-lock.json* ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build the application
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
EOF

cat > services/frontend/cloudrun-frontend.yaml << 'EOF'
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: laas-frontend
  namespace: default
  annotations:
    run.googleapis.com/ingress: all
    run.googleapis.com/ingress-status: all
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/cpu-throttling: "false"
        autoscaling.knative.dev/minScale: "0"
        autoscaling.knative.dev/maxScale: "50"
        run.googleapis.com/execution-environment: gen2
    spec:
      containerConcurrency: 1000
      timeoutSeconds: 300
      containers:
        - image: $(REGION)-docker.pkg.dev/$(PROJECT_ID)/laas/laas-frontend:$(REVISION)
          ports:
            - containerPort: 3000
          env:
            - name: ENVIRONMENT
              value: production
            - name: NEXT_PUBLIC_API_URL
              value: "https://laas-api-core-$(PROJECT_ID).$(REGION).run.app"
            - name: NEXT_PUBLIC_APP_URL
              value: "https://laas-frontend-$(PROJECT_ID).$(REGION).run.app"
            - name: GOOGLE_CLOUD_PROJECT_ID
              value: $(PROJECT_ID)
            - name: GOOGLE_CLOUD_REGION
              value: $(REGION)
            - name: NODE_ENV
              value: "production"
          resources:
            limits:
              cpu: "1"
              memory: 1Gi
            requests:
              cpu: "0.5"
              memory: 512Mi
          livenessProbe:
            httpGet:
              path: /api/health
              port: 3000
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /api/health
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
EOF

echo "✅ Created frontend structure"

# Create updated docker-compose for local development
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # Core API Service
  core-api:
    build:
      context: ./services/core-api
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - DATABASE_URL=postgresql://laas_user:laas_password@db:5432/laas_platform
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET_KEY=dev-secret-key
      - SECRET_KEY=dev-secret-key
    depends_on:
      - db
      - redis
    volumes:
      - ./services/core-api:/app
    command: uvicorn laas.main:app --host 0.0.0.0 --port 8000 --reload

  # Tenant API Service
  tenant-api:
    build:
      context: ./services/tenant-api
      dockerfile: Dockerfile
    ports:
      - "8001:8000"
    environment:
      - ENVIRONMENT=development
      - TENANT_ID=dev-tenant
      - DATABASE_URL=postgresql://laas_user:laas_password@db:5432/laas_platform
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET_KEY=dev-secret-key
      - SECRET_KEY=dev-secret-key
    depends_on:
      - db
      - redis
    volumes:
      - ./services/tenant-api:/app
    command: uvicorn laas.main:app --host 0.0.0.0 --port 8000 --reload

  # Frontend Service
  frontend:
    build:
      context: ./services/frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_APP_URL=http://localhost:3000
    volumes:
      - ./services/frontend:/app
      - /app/node_modules
    command: npm run dev

  # Database
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=laas_platform
      - POSTGRES_USER=laas_user
      - POSTGRES_PASSWORD=laas_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql

  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
EOF

echo "✅ Created updated docker-compose.yml"

# Create root README
cat > README.md << 'EOF'
# LAAS Platform - Monorepo

A comprehensive, multi-tenant API platform for building listing applications.

## 🏗️ Project Structure

```
laas-platform-dev/
├── services/                    # All API services
│   ├── core-api/              # Main LAAS Platform API
│   ├── tenant-api/            # Tenant-specific API instances
│   └── frontend/              # Control Panel Frontend
├── shared/                    # Shared libraries and utilities
├── infrastructure/            # Infrastructure as Code
├── docs/                      # Documentation
└── tests/                     # Integration and E2E tests
```

## 🚀 Quick Start

### Local Development
```bash
# Start all services
docker-compose up

# Start specific service
docker-compose up core-api
```

### Deployment
```bash
# Deploy all services
./infrastructure/scripts/deploy.sh all

# Deploy specific service
./infrastructure/scripts/deploy.sh core-api
```

## 📚 Documentation

- [Development Guide](docs/development/DEVELOPMENT_STRUCTURE.md)
- [Deployment Guide](docs/deployment/DEPLOYMENT.md)
- [Cloud Run Strategy](docs/deployment/CLOUD_RUN_STRATEGY.md)
- [Project Summary](docs/PROJECT_SUMMARY.md)

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=services tests/
```

## 🔧 Development

Each service can be developed independently:

- **Core API**: `cd services/core-api`
- **Tenant API**: `cd services/tenant-api`
- **Frontend**: `cd services/frontend`

## 📊 Services

### Core API (Port 8000)
- Main LAAS Platform API
- Multi-tenant management
- Admin operations

### Tenant API (Port 8001)
- Tenant-specific API instances
- Isolated tenant operations
- Custom tenant configurations

### Frontend (Port 3000)
- Control Panel Frontend
- Admin interface
- Tenant management

## 🎯 Next Steps

1. **Set up your environment**: Copy `.env.example` to `.env`
2. **Start development**: Run `docker-compose up`
3. **Deploy to Cloud Run**: Follow the deployment guide
4. **Add your frontend**: Develop your control panel in `services/frontend/`

## 📞 Support

For questions or issues:
1. Check the documentation in `docs/`
2. Review the deployment guides
3. Check the GitHub issues
4. Contact your system administrator
EOF

echo "✅ Created root README.md"

# Create .env.example
cat > .env.example << 'EOF'
# Environment
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://laas_user:laas_password@localhost:5432/laas_platform

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Security
SECRET_KEY=your-secret-key-here

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://localhost:8001
CORS_ALLOW_CREDENTIALS=true

# Google Cloud
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_CLOUD_REGION=us-central1

# Monitoring
SENTRY_DSN=your-sentry-dsn-here
LOG_LEVEL=INFO

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
EOF

echo "✅ Created .env.example"

# Update .gitignore
cat >> .gitignore << 'EOF'

# Monorepo specific
services/*/node_modules/
services/*/.next/
services/*/dist/
services/*/build/

# Shared libraries
shared/__pycache__/
shared/*.pyc

# Infrastructure
infrastructure/terraform/.terraform/
infrastructure/terraform/terraform.tfstate*

# Documentation
docs/_build/
docs/.doctrees/

# Tests
tests/__pycache__/
tests/.pytest_cache/
tests/coverage/
EOF

echo "✅ Updated .gitignore"

echo ""
echo "🎉 Migration completed successfully!"
echo ""
echo "📁 New project structure:"
echo "├── services/"
echo "│   ├── core-api/          # Your existing LAAS API"
echo "│   ├── tenant-api/        # Tenant-specific API template"
echo "│   └── frontend/          # Control Panel Frontend"
echo "├── shared/                # Shared libraries"
echo "├── infrastructure/        # Deployment configurations"
echo "├── docs/                  # Documentation"
echo "└── tests/                 # Integration tests"
echo ""
echo "🚀 Next steps:"
echo "1. Copy .env.example to .env and configure your settings"
echo "2. Run 'docker-compose up' to start local development"
echo "3. Develop your frontend in services/frontend/"
echo "4. Deploy using ./infrastructure/scripts/deploy.sh"
echo ""
echo "📚 Documentation is available in the docs/ directory"
echo ""
