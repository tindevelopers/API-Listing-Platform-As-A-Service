-- LAAS Platform Database Initialization Script
-- This script sets up the initial database structure and configurations

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "unaccent";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Create schemas for multi-tenant isolation
CREATE SCHEMA IF NOT EXISTS tenant_management;
CREATE SCHEMA IF NOT EXISTS laas_core;

-- Set up Row Level Security (RLS) for multi-tenant isolation
-- This will be applied to tables after they are created by SQLAlchemy

-- Create function to get current tenant ID
CREATE OR REPLACE FUNCTION app.current_tenant_id()
RETURNS UUID AS $$
BEGIN
    RETURN COALESCE(
        current_setting('app.current_tenant_id', true)::UUID,
        '00000000-0000-0000-0000-000000000000'::UUID
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION app.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create function for audit logging
CREATE OR REPLACE FUNCTION app.audit_trigger()
RETURNS TRIGGER AS $$
DECLARE
    tenant_id UUID;
    user_id UUID;
BEGIN
    -- Get tenant and user context
    tenant_id := app.current_tenant_id();
    user_id := COALESCE(
        current_setting('app.current_user_id', true)::UUID,
        NULL
    );
    
    -- Insert audit log
    INSERT INTO audit_logs (
        tenant_id,
        user_id,
        action,
        resource_type,
        resource_id,
        old_values,
        new_values,
        ip_address,
        user_agent,
        request_id
    ) VALUES (
        tenant_id,
        user_id,
        TG_OP,
        TG_TABLE_NAME,
        COALESCE(NEW.id::TEXT, OLD.id::TEXT),
        CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD) ELSE NULL END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW) ELSE NULL END,
        current_setting('app.client_ip', true),
        current_setting('app.user_agent', true),
        current_setting('app.request_id', true)
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create indexes for performance optimization
-- These will be created after tables are created by SQLAlchemy

-- Create full-text search configuration
CREATE TEXT SEARCH CONFIGURATION IF NOT EXISTS laas_search (COPY = english);

-- Add custom dictionary for better search results
-- This can be customized per tenant/industry

-- Create function to update search vector for listings
CREATE OR REPLACE FUNCTION app.update_listing_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('laas_search', 
        COALESCE(NEW.title, '') || ' ' || 
        COALESCE(NEW.description, '') || ' ' ||
        COALESCE(NEW.address, '') || ' ' ||
        COALESCE(NEW.city, '') || ' ' ||
        COALESCE(NEW.state, '') || ' ' ||
        COALESCE(NEW.country, '') || ' ' ||
        COALESCE(array_to_string(NEW.tags, ' '), '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for search vector updates
CREATE TRIGGER update_listing_search_vector_trigger
    BEFORE INSERT OR UPDATE ON listings
    FOR EACH ROW
    EXECUTE FUNCTION app.update_listing_search_vector();

-- Create GIN index for full-text search
CREATE INDEX IF NOT EXISTS idx_listings_search_vector 
ON listings USING GIN(search_vector);

-- Create function for geospatial distance calculation
CREATE OR REPLACE FUNCTION app.calculate_distance(
    lat1 DECIMAL, lon1 DECIMAL, 
    lat2 DECIMAL, lon2 DECIMAL
) RETURNS DECIMAL AS $$
BEGIN
    RETURN ST_Distance(
        ST_Point(lon1, lat1)::geography,
        ST_Point(lon2, lat2)::geography
    ) / 1609.344; -- Convert meters to miles
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Set up connection pooling and performance settings
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET track_activity_query_size = 2048;
ALTER SYSTEM SET pg_stat_statements.track = 'all';

-- Create default tenant for development
INSERT INTO tenants (
    id,
    name,
    subdomain,
    industry,
    status,
    plan,
    settings,
    branding
) VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID,
    'LAAS Development',
    'dev',
    'general',
    'active',
    'enterprise',
    '{"debug": true, "features": ["all"]}'::JSON,
    '{"primary_color": "#3B82F6", "logo_url": null}'::JSON
) ON CONFLICT (subdomain) DO NOTHING;

-- Create default admin user for development
INSERT INTO users (
    id,
    tenant_id,
    email,
    password_hash,
    first_name,
    last_name,
    role,
    status,
    email_verified
) VALUES (
    '00000000-0000-0000-0000-000000000002'::UUID,
    '00000000-0000-0000-0000-000000000001'::UUID,
    'admin@laas-platform.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzKzqK', -- password: admin123
    'Admin',
    'User',
    'superadmin',
    'active',
    true
) ON CONFLICT (tenant_id, email) DO NOTHING;

-- Create default industry schema for general listings
INSERT INTO industry_schemas (
    id,
    tenant_id,
    industry,
    version,
    name,
    description,
    fields,
    searchable_fields,
    required_fields,
    business_rules,
    is_active,
    is_default
) VALUES (
    '00000000-0000-0000-0000-000000000003'::UUID,
    '00000000-0000-0000-0000-000000000001'::UUID,
    'general',
    '1.0',
    'General Listing Schema',
    'Default schema for general listings',
    '[
        {
            "name": "title",
            "type": "text",
            "required": true,
            "display_name": "Title",
            "description": "Listing title"
        },
        {
            "name": "description",
            "type": "text",
            "required": false,
            "display_name": "Description",
            "description": "Detailed description"
        },
        {
            "name": "price",
            "type": "number",
            "required": false,
            "display_name": "Price",
            "description": "Listing price"
        },
        {
            "name": "category",
            "type": "enum",
            "required": false,
            "display_name": "Category",
            "description": "Listing category",
            "options": ["general", "services", "products", "events"]
        }
    ]'::JSON,
    '["title", "description", "category"]'::TEXT[],
    '["title"]'::TEXT[],
    '{"max_title_length": 255, "max_description_length": 5000}'::JSON,
    true,
    true
) ON CONFLICT (tenant_id, industry, version) DO NOTHING;

-- Create default categories
INSERT INTO categories (
    id,
    tenant_id,
    name,
    slug,
    description,
    icon,
    color,
    level,
    sort_order,
    is_active,
    is_featured
) VALUES 
    ('00000000-0000-0000-0000-000000000004'::UUID, '00000000-0000-0000-0000-000000000001'::UUID, 'General', 'general', 'General listings', 'folder', '#3B82F6', 0, 1, true, true),
    ('00000000-0000-0000-0000-000000000005'::UUID, '00000000-0000-0000-0000-000000000001'::UUID, 'Services', 'services', 'Service listings', 'briefcase', '#10B981', 0, 2, true, true),
    ('00000000-0000-0000-0000-000000000006'::UUID, '00000000-0000-0000-0000-000000000001'::UUID, 'Products', 'products', 'Product listings', 'shopping-bag', '#F59E0B', 0, 3, true, true),
    ('00000000-0000-0000-0000-000000000007'::UUID, '00000000-0000-0000-0000-000000000001'::UUID, 'Events', 'events', 'Event listings', 'calendar', '#EF4444', 0, 4, true, true)
ON CONFLICT (tenant_id, slug) DO NOTHING;

-- Create default tags
INSERT INTO tags (
    id,
    tenant_id,
    name,
    slug,
    description,
    color,
    usage_count,
    is_active
) VALUES 
    ('00000000-0000-0000-0000-000000000008'::UUID, '00000000-0000-0000-0000-000000000001'::UUID, 'Featured', 'featured', 'Featured listings', '#F59E0B', 0, true),
    ('00000000-0000-0000-0000-000000000009'::UUID, '00000000-0000-0000-0000-000000000001'::UUID, 'New', 'new', 'New listings', '#10B981', 0, true),
    ('00000000-0000-0000-0000-000000000010'::UUID, '00000000-0000-0000-0000-000000000001'::UUID, 'Popular', 'popular', 'Popular listings', '#EF4444', 0, true),
    ('00000000-0000-0000-0000-000000000011'::UUID, '00000000-0000-0000-0000-000000000001'::UUID, 'Verified', 'verified', 'Verified listings', '#3B82F6', 0, true)
ON CONFLICT (tenant_id, slug) DO NOTHING;

-- Create default API key for development
INSERT INTO api_keys (
    id,
    tenant_id,
    user_id,
    name,
    key_hash,
    key_prefix,
    permissions,
    rate_limit,
    is_active
) VALUES (
    '00000000-0000-0000-0000-000000000012'::UUID,
    '00000000-0000-0000-0000-000000000001'::UUID,
    '00000000-0000-0000-0000-000000000002'::UUID,
    'Development API Key',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzKzqK', -- Hash of 'dev-key-123'
    'dev_',
    '["read", "write", "admin"]'::TEXT[],
    10000,
    true
) ON CONFLICT DO NOTHING;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO laas_user;
GRANT USAGE ON SCHEMA tenant_management TO laas_user;
GRANT USAGE ON SCHEMA laas_core TO laas_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO laas_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO laas_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO laas_user;

-- Create indexes for better performance
-- These will be created after tables are created by SQLAlchemy migrations

COMMENT ON DATABASE laas_platform IS 'LAAS Platform - Listing Platform as a Service Database';
