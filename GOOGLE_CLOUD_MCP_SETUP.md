# Google Cloud MCP Servers Setup Guide

## Overview
This guide provides the exact commands that successfully set up Google Cloud MCP (Model Context Protocol) servers for local development with Cursor IDE.

## Prerequisites Check
Before starting, verify your current setup:

```bash
# Check Node.js version
node --version
# Expected: v22.16.0 or similar

# Check npm version  
npm --version
# Expected: v10.9.2 or similar

# Check Google Cloud CLI
gcloud --version
# Expected: Google Cloud SDK 538.0.0 or similar
```

## Step 1: Verify Node.js Installation ✅
Node.js v22.16.0 was already installed and working.

```bash
node --version && npm --version
```

## Step 2: Verify Google Cloud CLI Installation ✅
Google Cloud SDK 538.0.0 was already installed.

```bash
gcloud --version
```

## Step 3: Check Authentication Status
Verify existing authentication:

```bash
# Check authenticated accounts
gcloud auth list

# Check current project
gcloud config get-value project

# Check application default credentials
gcloud auth application-default print-access-token > /dev/null 2>&1 && echo "Application default credentials are set" || echo "Application default credentials need to be set"
```

## Step 4: Set Up Application Default Credentials
This was the key missing piece that needed to be configured:

```bash
gcloud auth application-default login
```

**Expected Output:**
```
Your browser has been opened to visit:
https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=...

Credentials saved to file: [/Users/foo/.config/gcloud/application_default_credentials.json]

These credentials will be used by any library that requests Application Default Credentials (ADC).

Quota project "sdk-ai-blog-writer" was added to ADC which can be used by Google client libraries for billing and quota.
```

## Step 5: Test MCP Servers Installation
Install and test all three Google Cloud MCP servers:

```bash
# Test Cloud Run MCP
npx -y @google-cloud/cloud-run-mcp --help

# Test gcloud MCP  
npx -y @google-cloud/gcloud-mcp --help

# Test Observability MCP
npx -y @google-cloud/observability-mcp --help
```

**Expected Output for Cloud Run MCP:**
```
Checking for Google Cloud Application Default Credentials...
Application Default Credentials found.
Using tools optimized for local or stdio mode.
Cloud Run MCP server stdio transport connected
```

## Step 6: Update Global Cursor MCP Configuration
The critical step was updating the global Cursor MCP configuration file:

**File Location:** `~/.cursor/mcp.json`

**Add these entries to your existing mcpServers configuration:**

```json
{
  "mcpServers": {
    "cloud-run": {
      "command": "npx",
      "args": ["-y", "@google-cloud/cloud-run-mcp"]
    },
    "gcloud": {
      "command": "npx", 
      "args": ["-y", "@google-cloud/gcloud-mcp"]
    },
    "observability": {
      "command": "npx",
      "args": ["-y", "@google-cloud/observability-mcp"]
    }
  }
}
```

## Step 7: Verify Final Setup
Confirm everything is working:

```bash
# Verify application default credentials
gcloud auth application-default print-access-token > /dev/null 2>&1 && echo "✅ Application default credentials are working" || echo "❌ Application default credentials still need setup"

# Test Cloud Run MCP with authentication
npx -y @google-cloud/cloud-run-mcp --help | head -10
```

## Available MCP Servers

### 1. Cloud Run MCP (`@google-cloud/cloud-run-mcp`)
- **Purpose:** Deploy, manage, and monitor Cloud Run services
- **Version:** 1.5.0
- **Features:** Service deployment, scaling, monitoring

### 2. gcloud MCP (`@google-cloud/gcloud-mcp`) 
- **Purpose:** Execute gcloud CLI commands through MCP
- **Version:** 0.1.1
- **Features:** General Google Cloud operations

### 3. Observability MCP (`@google-cloud/observability-mcp`)
- **Purpose:** Monitor and debug applications
- **Version:** 0.1.1  
- **Features:** Logs, metrics, traces, alerts

## Troubleshooting

### Common Issues:

1. **"Application Default Credentials are not set up"**
   - **Solution:** Run `gcloud auth application-default login`

2. **MCP servers not showing in Cursor**
   - **Solution:** Ensure configuration is in `~/.cursor/mcp.json` (global), not local project file
   - **Solution:** Restart Cursor after updating configuration

3. **Authentication errors**
   - **Solution:** Verify project is set: `gcloud config set project your-project-id`
   - **Solution:** Check active account: `gcloud auth list`

## Final Configuration Summary

**Authentication:**
- ✅ User authentication: `blog-writer-prod@sdk-ai-blog-writer.iam.gserviceaccount.com`
- ✅ Application default credentials: `/Users/foo/.config/gcloud/application_default_credentials.json`
- ✅ Project: `sdk-ai-blog-writer`

**MCP Servers:**
- ✅ Cloud Run MCP: Ready and authenticated
- ✅ gcloud MCP: Ready to use
- ✅ Observability MCP: Ready to use

**Cursor Integration:**
- ✅ Global MCP configuration updated in `~/.cursor/mcp.json`
- ✅ All servers configured with proper npx commands

## Next Steps
1. Restart Cursor IDE to load the updated MCP configuration
2. The Google Cloud MCP tools should now appear in Cursor's MCP interface
3. Begin using the tools for Cloud Run deployments, gcloud operations, and observability monitoring

---
*Generated on: September 17, 2024*
*Project: API-Listing-Platform-As-A-Service*
