#!/bin/bash

echo "🔍 Verifying MCP Setup for Cursor..."

# Check if MCP configuration files exist
echo "📁 Checking MCP configuration files..."

if [ -f "$HOME/.cursor/mcp.json" ]; then
    echo "⚠️  Global MCP config found (should be removed for project-only setup)"
else
    echo "✅ No global MCP config (project-only setup)"
fi

if [ -f ".cursor/mcp.json" ]; then
    echo "✅ Project MCP config found: .cursor/mcp.json"
else
    echo "❌ Project MCP config missing: .cursor/mcp.json"
fi

# Check Node.js and npm
echo ""
echo "🔧 Checking prerequisites..."

if command -v node &> /dev/null; then
    echo "✅ Node.js installed: $(node --version)"
else
    echo "❌ Node.js not found"
fi

if command -v npm &> /dev/null; then
    echo "✅ npm installed: $(npm --version)"
else
    echo "❌ npm not found"
fi

# Check Python environment
echo ""
echo "🐍 Checking Python environment..."

if [ -d "venv" ]; then
    echo "✅ Python virtual environment found"
    if source venv/bin/activate 2>/dev/null && python -c "import mcp" 2>/dev/null; then
        echo "✅ MCP Python package installed"
    else
        echo "❌ MCP Python package not found in venv"
    fi
else
    echo "❌ Python virtual environment not found"
fi

# Check service account key
echo ""
echo "🔐 Checking authentication..."

if [ -f "service-account-key.json" ]; then
    echo "✅ Service account key found"
else
    echo "⚠️  Service account key missing (create from template)"
    echo "   Template available: service-account-key.json.template"
fi

# Check Google Cloud CLI
if command -v gcloud &> /dev/null; then
    echo "✅ Google Cloud CLI installed: $(gcloud --version | head -n1)"
else
    echo "❌ Google Cloud CLI not found"
fi

echo ""
echo "📋 Next steps:"
echo "1. Restart Cursor completely"
echo "2. Check Cursor Settings → MCP section"
echo "3. You should see 2 MCP servers: filesystem and memory"
echo "4. Google Cloud integration works through existing CLI tools"
echo ""
echo "📖 See CURSOR_MCP_SETUP.md for detailed instructions"
