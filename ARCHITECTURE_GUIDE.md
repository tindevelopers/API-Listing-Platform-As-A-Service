# Multi-Tenant Listing Platform Architecture Guide

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture Design](#architecture-design)
3. [Technology Stack](#technology-stack)
4. [Database Schema](#database-schema)
5. [API Endpoints](#api-endpoints)
6. [Implementation Guide](#implementation-guide)
7. [Client Integration](#client-integration)
8. [Deployment Strategy](#deployment-strategy)

---

## 🎯 Overview

This platform is a **Multi-Tenant SaaS API** for building listing platforms (real estate, job boards, marketplaces, etc.) with built-in support for:

- **Listings Management** - Create, read, update, delete listings
- **Reviews & Ratings** - User reviews with moderation
- **Bookings & Reservations** - Date-based booking system
- **Multi-Tenancy** - Complete data isolation per client
- **Flexible Schema** - Customizable fields per tenant/industry

### What This Platform Provides

**You Build (Backend):**
- Single Python FastAPI service (Cloud Run)
- Multi-tenant API with data isolation
- Business logic for all features
- Connected to Supabase database

**Clients Build (Frontend):**
- Their own UI in any framework (React, Vue, Angular, etc.)
- Mobile apps (React Native, Flutter)
- WordPress plugins, Shopify apps, etc.
- Any frontend technology they choose

---

## 🏗️ Architecture Design

### High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│  CLIENT APPLICATIONS (Customer Frontends)           │
│  - Real Estate App (React)                          │
│  - Job Board (Vue.js)                               │
│  - Marketplace (Next.js)                            │
│  - Mobile App (React Native)                        │
└─────────────────────────────────────────────────────┘
                      ↓ API Requests
┌─────────────────────────────────────────────────────┐
│  PYTHON BACKEND (Cloud Run + FastAPI)               │
│  - Multi-tenant API                                 │
│  - Business logic                                   │
│  - Authentication & Authorization                   │
│  - Tenant routing middleware                        │
└─────────────────────────────────────────────────────┘
                      ↓ Connects to
┌─────────────────────────────────────────────────────┐
│  SUPABASE                                           │
│  - PostgreSQL Database (multi-tenant)               │
│  - Authentication (built-in)                        │
│  - Row-Level Security (tenant isolation)            │
│  - Real-time subscriptions                          │
│  - File storage (images/documents)                  │
└─────────────────────────────────────────────────────┘
```

### Request Flow

```
Customer App (tenant123.com)
    ↓ HTTP Request
API Gateway (api.yourplatform.com)
    ↓ Runs on
Google Cloud Run (FastAPI)
    ↓ Extracts Tenant
Tenant Middleware: "tenant_id = tenant123"
    ↓ Queries Database
Supabase PostgreSQL
    ↓ Row-Level Security
Returns ONLY tenant123's data
    ↓ Response
Back to Customer App
```

---

## 🛠️ Technology Stack

### Backend (Your Responsibility)

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Runtime** | Python 3.11+ | Application language |
| **Framework** | FastAPI | REST API framework |
| **Hosting** | Google Cloud Run | Serverless container platform |
| **Database** | Supabase (PostgreSQL) | Multi-tenant data storage |
| **Authentication** | Supabase Auth | User authentication |
| **File Storage** | Supabase Storage | Images, documents |
| **Real-time** | Supabase Realtime | Live updates |
| **CI/CD** | GitHub Actions | Automated deployment |

### Frontend (Client's Responsibility)

Clients can use **any** frontend technology:
- React, Vue, Angular, Svelte
- Next.js, Nuxt, Remix
- React Native, Flutter
- WordPress, Shopify
- Vanilla JavaScript

---

## 📊 Database Schema

### Core Tables

#### 1. Tenants Table

```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    subdomain TEXT UNIQUE NOT NULL,
    industry TEXT, -- 'real_estate', 'jobs', 'marketplace'
    config JSONB DEFAULT '{}',
    plan TEXT DEFAULT 'free',
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row-Level Security
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own tenant
CREATE POLICY "Users can view own tenant"
    ON tenants FOR SELECT
    USING (auth.uid() IN (
        SELECT user_id FROM tenant_users WHERE tenant_id = id
    ));
```

#### 2. Listings Table

```sql
CREATE TABLE listings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    owner_id UUID REFERENCES auth.users(id),
    
    -- Basic fields
    title TEXT NOT NULL,
    description TEXT,
    slug TEXT,
    
    -- Pricing
    price DECIMAL(10,2),
    currency TEXT DEFAULT 'USD',
    
    -- Location
    city TEXT,
    state TEXT,
    country TEXT,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    
    -- Flexible schema per tenant
    custom_fields JSONB DEFAULT '{}',
    
    -- Status
    status TEXT DEFAULT 'draft',
    is_public BOOLEAN DEFAULT true,
    
    -- Metrics
    average_rating DECIMAL(3,2),
    review_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS for tenant isolation
ALTER TABLE listings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation for listings"
    ON listings FOR ALL
    USING (tenant_id IN (
        SELECT tenant_id FROM tenant_users WHERE user_id = auth.uid()
    ));

-- Indexes
CREATE INDEX idx_listings_tenant ON listings(tenant_id);
CREATE INDEX idx_listings_status ON listings(status);
CREATE INDEX idx_listings_location ON listings(city, state, country);
```

#### 3. Reviews Table

```sql
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    listing_id UUID REFERENCES listings(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id),
    
    -- Review content
    rating INTEGER CHECK (rating >= 1 AND rating <= 5) NOT NULL,
    title TEXT,
    comment TEXT,
    
    -- Review metadata
    status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    is_verified BOOLEAN DEFAULT false,
    helpful_count INTEGER DEFAULT 0,
    
    -- Photos (optional)
    photos JSONB DEFAULT '[]',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Prevent duplicate reviews
    UNIQUE(tenant_id, listing_id, user_id)
);

-- RLS
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation for reviews"
    ON reviews FOR ALL
    USING (tenant_id IN (
        SELECT tenant_id FROM tenant_users WHERE user_id = auth.uid()
    ));

-- Indexes
CREATE INDEX idx_reviews_listing ON reviews(listing_id);
CREATE INDEX idx_reviews_user ON reviews(user_id);
CREATE INDEX idx_reviews_tenant ON reviews(tenant_id);
CREATE INDEX idx_reviews_status ON reviews(status);
```

#### 4. Bookings Table

```sql
CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    listing_id UUID REFERENCES listings(id) ON DELETE CASCADE,
    
    -- Who's booking
    user_id UUID REFERENCES auth.users(id),
    guest_name TEXT NOT NULL,
    guest_email TEXT NOT NULL,
    guest_phone TEXT,
    
    -- Booking details
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    guests_count INTEGER NOT NULL,
    
    -- Pricing
    price_per_night DECIMAL(10,2),
    total_nights INTEGER,
    subtotal DECIMAL(10,2),
    fees DECIMAL(10,2) DEFAULT 0,
    taxes DECIMAL(10,2) DEFAULT 0,
    total_price DECIMAL(10,2) NOT NULL,
    currency TEXT DEFAULT 'USD',
    
    -- Status
    status TEXT DEFAULT 'pending', -- 'pending', 'confirmed', 'cancelled', 'completed'
    payment_status TEXT DEFAULT 'unpaid', -- 'unpaid', 'paid', 'refunded'
    
    -- Special requests
    special_requests TEXT,
    custom_fields JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    cancelled_at TIMESTAMPTZ,
    
    -- Prevent double booking
    CONSTRAINT no_overlap EXCLUDE USING GIST (
        listing_id WITH =,
        daterange(check_in_date, check_out_date) WITH &&
    ) WHERE (status NOT IN ('cancelled'))
);

-- RLS
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation for bookings"
    ON bookings FOR ALL
    USING (tenant_id IN (
        SELECT tenant_id FROM tenant_users WHERE user_id = auth.uid()
    ));

-- Indexes
CREATE INDEX idx_bookings_listing ON bookings(listing_id);
CREATE INDEX idx_bookings_user ON bookings(user_id);
CREATE INDEX idx_bookings_dates ON bookings(check_in_date, check_out_date);
CREATE INDEX idx_bookings_status ON bookings(status);
```

#### 5. Tenant Users (Join Table)

```sql
CREATE TABLE tenant_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'user', -- 'owner', 'admin', 'user'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, user_id)
);

-- RLS
ALTER TABLE tenant_users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own tenant memberships"
    ON tenant_users FOR SELECT
    USING (user_id = auth.uid());
```

---

## 🔌 API Endpoints

### Listings Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/listings` | Get all listings for tenant |
| `GET` | `/api/v1/listings/{id}` | Get single listing |
| `POST` | `/api/v1/listings` | Create new listing |
| `PUT` | `/api/v1/listings/{id}` | Update listing |
| `DELETE` | `/api/v1/listings/{id}` | Delete listing |
| `GET` | `/api/v1/listings/search` | Search listings |

### Reviews Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/listings/{id}/reviews` | Get reviews for listing |
| `POST` | `/api/v1/reviews` | Create review |
| `PATCH` | `/api/v1/reviews/{id}/moderate` | Moderate review (admin) |
| `POST` | `/api/v1/reviews/{id}/helpful` | Mark review as helpful |

### Bookings Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/bookings/check-availability` | Check availability |
| `GET` | `/api/v1/bookings` | Get user's bookings |
| `POST` | `/api/v1/bookings` | Create booking |
| `GET` | `/api/v1/bookings/{id}` | Get booking details |
| `PATCH` | `/api/v1/bookings/{id}/cancel` | Cancel booking |
| `PATCH` | `/api/v1/bookings/{id}/confirm` | Confirm booking |

### Authentication

All endpoints require:
- **Authorization Header**: `Bearer {jwt_token}`
- **Tenant Identification**: One of:
  - Header: `X-Tenant-ID: {tenant_id}`
  - Subdomain: `{tenant}.api.com`
  - Query param: `?tenant_id={tenant_id}`

---

## 💻 Implementation Guide

### Project Structure

```
laas/
├── main.py                    # FastAPI app
├── core/
│   └── config.py             # Settings & configuration
├── middleware/
│   ├── tenant.py             # Tenant extraction
│   ├── rate_limit.py         # Rate limiting
│   └── audit.py              # Audit logging
├── api/
│   └── v1/
│       ├── endpoints/
│       │   ├── listings.py   # Listing endpoints
│       │   ├── reviews.py    # Review endpoints
│       │   ├── bookings.py   # Booking endpoints
│       │   └── auth.py       # Auth endpoints
│       └── router.py         # API router
├── services/
│   ├── listing_service.py    # Listing business logic
│   ├── review_service.py     # Review business logic
│   └── booking_service.py    # Booking business logic
├── database/
│   ├── supabase_client.py   # Supabase connection
│   └── models.py            # Pydantic models
└── schemas/
    ├── listing.py           # Listing schemas
    ├── review.py            # Review schemas
    └── booking.py           # Booking schemas
```

### Supabase Configuration

```python
# laas/core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Supabase
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_key: str = Field(..., alias="SUPABASE_KEY")
    supabase_service_role_key: str = Field(..., alias="SUPABASE_SERVICE_ROLE_KEY")
    
    # API
    api_version: str = "1.0.0"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        populate_by_name = True
```

```python
# laas/database/supabase_client.py
from supabase import create_client, Client
from laas.core.config import get_settings

settings = get_settings()

# Public client (uses RLS)
supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_key
)

# Admin client (bypasses RLS)
supabase_admin: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_role_key
)
```

### Tenant Middleware

```python
# laas/middleware/tenant.py
from fastapi import Request, HTTPException
from uuid import UUID

async def extract_tenant_id(request: Request) -> UUID:
    """Extract tenant ID from request"""
    
    # Method 1: From header
    tenant_id = request.headers.get("X-Tenant-ID")
    
    # Method 2: From subdomain
    if not tenant_id:
        host = request.headers.get("host", "")
        if "." in host:
            subdomain = host.split(".")[0]
            # Lookup tenant by subdomain
            # tenant = await get_tenant_by_subdomain(subdomain)
            # tenant_id = tenant.id
    
    # Method 3: From query params
    if not tenant_id:
        tenant_id = request.query_params.get("tenant_id")
    
    if not tenant_id:
        raise HTTPException(
            status_code=400, 
            detail="Tenant ID required"
        )
    
    return UUID(tenant_id)

async def get_current_tenant(request: Request) -> UUID:
    """Dependency for getting current tenant"""
    return await extract_tenant_id(request)
```

### Service Layer Example

```python
# laas/services/review_service.py
from typing import List
from uuid import UUID
from laas.database.supabase_client import supabase

class ReviewService:
    
    async def get_listing_reviews(
        self,
        listing_id: UUID,
        tenant_id: UUID,
        status: str = "approved"
    ) -> List[dict]:
        """Get all reviews for a listing"""
        response = supabase.table("reviews")\
            .select("*")\
            .eq("listing_id", str(listing_id))\
            .eq("tenant_id", str(tenant_id))\
            .eq("status", status)\
            .order("created_at", desc=True)\
            .execute()
        
        return response.data
    
    async def create_review(
        self,
        tenant_id: UUID,
        listing_id: UUID,
        user_id: UUID,
        rating: int,
        title: str,
        comment: str
    ) -> dict:
        """Create a new review"""
        review_data = {
            "tenant_id": str(tenant_id),
            "listing_id": str(listing_id),
            "user_id": str(user_id),
            "rating": rating,
            "title": title,
            "comment": comment,
            "status": "pending"
        }
        
        response = supabase.table("reviews")\
            .insert(review_data)\
            .execute()
        
        return response.data[0]
```

### API Endpoint Example

```python
# laas/api/v1/endpoints/reviews.py
from fastapi import APIRouter, Depends
from uuid import UUID
from pydantic import BaseModel, Field
from laas.services.review_service import ReviewService
from laas.middleware.tenant import get_current_tenant

router = APIRouter()
review_service = ReviewService()

class ReviewCreate(BaseModel):
    listing_id: UUID
    rating: int = Field(..., ge=1, le=5)
    title: str = Field(..., max_length=200)
    comment: str = Field(..., max_length=2000)

@router.get("/listings/{listing_id}/reviews")
async def get_reviews(
    listing_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant)
):
    """Get all approved reviews for a listing"""
    reviews = await review_service.get_listing_reviews(
        listing_id=listing_id,
        tenant_id=tenant_id
    )
    return {"reviews": reviews, "count": len(reviews)}

@router.post("/reviews")
async def create_review(
    review: ReviewCreate,
    tenant_id: UUID = Depends(get_current_tenant),
    user_id: UUID = Depends(get_current_user)
):
    """Create a new review"""
    created = await review_service.create_review(
        tenant_id=tenant_id,
        listing_id=review.listing_id,
        user_id=user_id,
        rating=review.rating,
        title=review.title,
        comment=review.comment
    )
    return {"review": created}
```

---

## 🌐 Client Integration

### How Clients Use Your API

Clients build their frontend in **any technology** and make HTTP requests to your API.

### React Example

```javascript
// api/client.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'https://api.yourplatform.com',
  headers: {
    'X-Tenant-ID': process.env.REACT_APP_TENANT_ID
  }
});

// Add auth token to requests
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default apiClient;
```

```javascript
// services/listings.js
import apiClient from './client';

export const listingsAPI = {
  getAll: async (filters = {}) => {
    const response = await apiClient.get('/api/v1/listings', {
      params: filters
    });
    return response.data;
  },
  
  getById: async (id) => {
    const response = await apiClient.get(`/api/v1/listings/${id}`);
    return response.data;
  },
  
  create: async (data) => {
    const response = await apiClient.post('/api/v1/listings', data);
    return response.data;
  },
  
  getReviews: async (listingId) => {
    const response = await apiClient.get(
      `/api/v1/listings/${listingId}/reviews`
    );
    return response.data;
  }
};
```

```javascript
// components/ListingList.jsx
import { useState, useEffect } from 'react';
import { listingsAPI } from '../services/listings';

function ListingList() {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const fetchListings = async () => {
      try {
        const data = await listingsAPI.getAll();
        setListings(data.listings);
      } catch (error) {
        console.error('Error fetching listings:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchListings();
  }, []);
  
  if (loading) return <div>Loading...</div>;
  
  return (
    <div className="listing-grid">
      {listings.map(listing => (
        <ListingCard key={listing.id} listing={listing} />
      ))}
    </div>
  );
}
```

### Vue.js Example

```javascript
// composables/useListings.js
import { ref } from 'vue';
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'https://api.yourplatform.com',
  headers: {
    'X-Tenant-ID': import.meta.env.VITE_TENANT_ID
  }
});

export function useListings() {
  const listings = ref([]);
  const loading = ref(false);
  
  const fetchListings = async () => {
    loading.value = true;
    try {
      const { data } = await apiClient.get('/api/v1/listings');
      listings.value = data.listings;
    } finally {
      loading.value = false;
    }
  };
  
  const createReview = async (listingId, reviewData) => {
    const { data } = await apiClient.post('/api/v1/reviews', {
      listing_id: listingId,
      ...reviewData
    });
    return data.review;
  };
  
  return {
    listings,
    loading,
    fetchListings,
    createReview
  };
}
```

### Mobile (React Native) Example

```javascript
// services/api.js
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const api = axios.create({
  baseURL: 'https://api.yourplatform.com',
  headers: {
    'X-Tenant-ID': 'your-tenant-id'
  }
});

// Add auth token
api.interceptors.request.use(async config => {
  const token = await AsyncStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const bookingAPI = {
  checkAvailability: async (listingId, checkIn, checkOut) => {
    const { data } = await api.post('/api/v1/bookings/check-availability', {
      listing_id: listingId,
      check_in: checkIn,
      check_out: checkOut
    });
    return data;
  },
  
  createBooking: async (bookingData) => {
    const { data } = await api.post('/api/v1/bookings', bookingData);
    return data.booking;
  }
};
```

---

## 🚀 Deployment Strategy

### CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]

env:
  PROJECT_ID: your-project-id
  REGION: us-east1
  SERVICE_NAME: listing-platform

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Google Auth
      uses: google-github-actions/auth@v2
      with:
        credentials_json: ${{ secrets.GCP_SA_KEY }}
    
    - name: Build and Push Docker Image
      run: |
        docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/app/$SERVICE_NAME:$GITHUB_SHA .
        docker push $REGION-docker.pkg.dev/$PROJECT_ID/app/$SERVICE_NAME:$GITHUB_SHA
    
    - name: Deploy to Cloud Run
      run: |
        gcloud run deploy $SERVICE_NAME \
          --image=$REGION-docker.pkg.dev/$PROJECT_ID/app/$SERVICE_NAME:$GITHUB_SHA \
          --region=$REGION \
          --platform=managed \
          --allow-unauthenticated
```

### Environment Variables

Required secrets in GitHub Actions:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Google Cloud
GCP_SA_KEY={"type": "service_account", ...}
```

### Scaling Strategy

| Tier | Database | API | Use Case |
|------|----------|-----|----------|
| **Starter** | Shared Supabase | Single Cloud Run | Small tenants (< 1k users) |
| **Growth** | Shared Supabase | Auto-scaling Cloud Run | Medium tenants (1k-10k users) |
| **Enterprise** | Dedicated Supabase | Dedicated Cloud Run | Large tenants (> 10k users) |

---

## 📈 Feature Roadmap

### Phase 1: Core Platform (Current)
- ✅ Multi-tenant listings
- ✅ Reviews & ratings
- ✅ Bookings & reservations
- ✅ Cloud Run deployment
- ✅ Supabase integration

### Phase 2: Enhanced Features
- 📅 Payment integration (Stripe)
- 📅 Email notifications
- 📅 SMS notifications
- 📅 Advanced search (Elasticsearch)
- 📅 File uploads (images, documents)

### Phase 3: Analytics & Insights
- 📅 Tenant analytics dashboard
- 📅 Usage metrics
- 📅 Revenue tracking
- 📅 Performance monitoring

### Phase 4: Enterprise Features
- 📅 Custom domains
- 📅 White-labeling
- 📅 SSO integration
- 📅 SLA monitoring
- 📅 Dedicated instances

---

## 🔐 Security Best Practices

### Tenant Isolation

1. **Row-Level Security (RLS)** - All tables enforce tenant isolation
2. **Middleware Validation** - Every request validates tenant ID
3. **JWT Tokens** - Include tenant_id in token claims
4. **API Keys** - Tenant-specific API keys

### Data Protection

1. **Encryption at Rest** - Supabase encrypts all data
2. **Encryption in Transit** - HTTPS/TLS for all API calls
3. **Password Hashing** - Supabase Auth handles secure hashing
4. **Rate Limiting** - Prevent abuse and DDoS

### Access Control

1. **Role-Based Access** - Owner, Admin, User roles
2. **Resource Permissions** - Fine-grained access control
3. **Audit Logging** - Track all data changes
4. **Token Expiration** - Short-lived access tokens

---

## 📚 API Documentation

### Auto-Generated Docs

FastAPI provides automatic interactive documentation:

- **Swagger UI**: `https://api.yourplatform.com/docs`
- **ReDoc**: `https://api.yourplatform.com/redoc`
- **OpenAPI JSON**: `https://api.yourplatform.com/openapi.json`

### Client SDKs (Optional)

You can generate client SDKs from OpenAPI spec:

```bash
# JavaScript/TypeScript SDK
npx openapi-generator-cli generate \
  -i https://api.yourplatform.com/openapi.json \
  -g typescript-axios \
  -o ./sdk/typescript

# Python SDK
openapi-generator generate \
  -i https://api.yourplatform.com/openapi.json \
  -g python \
  -o ./sdk/python
```

---

## 🎯 Key Takeaways

1. **One Backend, Many Frontends** - Your Python API powers unlimited client applications
2. **Supabase = PostgreSQL + More** - Database, auth, storage, real-time in one platform
3. **Cloud Run = Serverless Simplicity** - Auto-scaling, no server management
4. **Multi-Tenancy = Data Isolation** - Each client's data is completely separate
5. **Flexible Schema** - Custom fields via JSONB for industry-specific needs
6. **Continue Building** - Add features (bookings, reviews, payments) to same service

---

## 📞 Support & Resources

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Supabase Docs](https://supabase.com/docs)
- [Cloud Run Docs](https://cloud.google.com/run/docs)

### Community
- GitHub Issues: Report bugs and feature requests
- Discord: Join our developer community
- Stack Overflow: Tag questions with `listing-platform`

---

**Last Updated**: October 2025  
**Version**: 1.0.0  
**Author**: LAAS Platform Team

