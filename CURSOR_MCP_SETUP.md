# Cursor MCP Setup Guide

This guide will help you set up Model Context Protocol (MCP) integration with Cursor for your LAAS platform.

## What We've Created

### 1. MCP Configuration Files
- **Project**: `.cursor/mcp.json` - Specific to this LAAS project only
- **Template**: `service-account-key.json.template` - Service account template

> **Note**: This setup uses project-only MCP configuration to avoid conflicts with other projects.

### 2. Configured MCP Servers
- **Filesystem**: Access to project files (14 tools enabled)
- **Memory**: Persistent memory for context (9 tools enabled)

> **Note**: Google Cloud integration is handled through the existing Google Cloud CLI and service account authentication, not through a separate MCP server.

## Setup Steps

### Step 1: Create Service Account Key

1. **Go to Google Cloud Console**:
   - Navigate to: https://console.cloud.google.com/iam-admin/serviceaccounts
   - Select project: `laas-platform-1758016737`

2. **Create Service Account**:
   - Click "Create Service Account"
   - Name: `cursor-mcp-service`
   - Description: "Service account for Cursor MCP integration"

3. **Assign Roles**:
   - Cloud Run Admin
   - Cloud Build Editor
   - Secret Manager Secret Accessor
   - Artifact Registry Writer

4. **Create Key**:
   - Click on the service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Choose JSON format
   - Download the key file

### Step 2: Configure Authentication

1. **Copy the downloaded JSON key** to your project:
   ```bash
   cp ~/Downloads/your-service-account-key.json ./service-account-key.json
   ```

2. **Update permissions**:
   ```bash
   chmod 600 service-account-key.json
   ```

### Step 3: Restart Cursor

1. **Close Cursor completely**
2. **Reopen Cursor**
3. **Open this project**

### Step 4: Verify MCP Integration

1. **Check Cursor Settings**:
   - Go to Cursor Settings (Cmd/Ctrl + ,)
   - Look for "MCP" section
   - You should see your configured servers

2. **Test MCP Commands**:
   - Try asking me to list Cloud Run services
   - Ask me to check your Google Cloud project status
   - Request deployment to Cloud Run

## Available MCP Servers

### Google Cloud Server
- **Purpose**: Direct Google Cloud integration
- **Capabilities**:
  - Deploy to Cloud Run
  - Manage secrets
  - Check service status
  - View logs
  - Scale services

### Filesystem Server
- **Purpose**: Access to project files
- **Capabilities**:
  - Read/write project files
  - Navigate directory structure
  - Edit configuration files

### Memory Server
- **Purpose**: Persistent context
- **Capabilities**:
  - Remember project context
  - Store deployment history
  - Track configuration changes

## Troubleshooting

### MCP Servers Not Appearing
1. **Check file locations**:
   ```bash
   ls -la ~/.cursor/mcp.json
   ls -la .cursor/mcp.json
   ```

2. **Verify JSON syntax**:
   ```bash
   cat ~/.cursor/mcp.json | python -m json.tool
   ```

3. **Restart Cursor completely**

### Authentication Issues
1. **Check service account key**:
   ```bash
   ls -la service-account-key.json
   ```

2. **Verify project ID**:
   ```bash
   gcloud config get-value project
   ```

3. **Test authentication**:
   ```bash
   gcloud auth activate-service-account --key-file=service-account-key.json
   gcloud auth list
   ```

### Server Connection Issues
1. **Check Node.js and npm**:
   ```bash
   node --version
   npm --version
   ```

2. **Test MCP server manually**:
   ```bash
   npx -y @google-cloud/mcp-server
   ```

## Next Steps

Once MCP is working in Cursor:

1. **Test Google Cloud Integration**:
   - Ask me to list your Cloud Run services
   - Request deployment status
   - Check project resources

2. **Set up GitHub Actions**:
   - Create automated deployment workflows
   - Configure CI/CD pipeline

3. **Deploy Your Application**:
   - Use MCP commands to deploy
   - Monitor deployment progress
   - Verify service health

## Support

If you encounter issues:

1. **Check Cursor logs**: Help → Toggle Developer Tools → Console
2. **Verify MCP configuration**: Ensure JSON syntax is correct
3. **Test individual components**: Verify each MCP server separately

## Security Notes

- **Never commit service account keys** to version control
- **Use environment variables** for sensitive data
- **Rotate keys regularly** for security
- **Limit service account permissions** to minimum required

