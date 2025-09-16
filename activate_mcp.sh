#!/bin/bash

# LAAS Platform MCP Environment Activation Script
echo "🚀 Activating LAAS Platform MCP Environment..."

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export GOOGLE_CLOUD_PROJECT="laas-platform-1758016737"
export GOOGLE_CLOUD_REGION="us-central1"
export MCP_CONFIG_PATH="./mcp_config.json"

# Verify MCP installation
echo "✅ Checking MCP installation..."
python -c "import mcp; print('MCP: Ready')" 2>/dev/null || echo "❌ MCP not installed"

# Verify Google Cloud integration
echo "✅ Checking Google Cloud integration..."
python -c "import google.cloud.run; print('Google Cloud Run: Ready')" 2>/dev/null || echo "❌ Google Cloud Run not installed"

echo "🎉 LAAS Platform MCP Environment activated!"
echo "📋 Available commands:"
echo "   - python -m mcp.server.google_cloud (start MCP server)"
echo "   - gcloud run services list (list Cloud Run services)"
echo "   - python -c 'import mcp; print(mcp.__version__)' (check MCP version)"
echo ""
echo "🔧 To use MCP with AI assistants, configure your client to connect to:"
echo "   - MCP Server: python -m mcp.server.google_cloud"
echo "   - Project: laas-platform-1758016737"
echo "   - Region: us-central1"

