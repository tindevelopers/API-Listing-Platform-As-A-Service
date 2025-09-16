# Google Model Context Protocol (MCP) Setup

This project now includes Google Model Context Protocol (MCP) integration for enhanced AI assistant capabilities with Google Cloud services.

## What is MCP?

Model Context Protocol (MCP) is a protocol that allows AI assistants to securely connect to external data sources and tools. In this project, MCP provides direct integration with Google Cloud services.

## Installation Status

✅ **MCP Package**: Version 1.14.0 installed  
✅ **Google Cloud Integration**: Cloud Run, Build, Secret Manager clients installed  
✅ **Python Environment**: Python 3.11 virtual environment configured  
✅ **Project Configuration**: MCP config file created  

## Quick Start

### 1. Activate MCP Environment
```bash
./activate_mcp.sh
```

### 2. Verify Installation
```bash
source venv/bin/activate
python -c "import mcp; print('MCP Ready!')"
```

### 3. Test Google Cloud Integration
```bash
source venv/bin/activate
python -c "import google.cloud.run; print('Google Cloud Run Ready!')"
```

## Available MCP Tools

With MCP installed, AI assistants can now:

- **Access Project Files**: Read and write files in your project directory
- **Persistent Memory**: Remember context across conversations
- **Google Cloud Integration**: Use existing CLI tools with service account authentication
  - Deploy to Cloud Run via `gcloud run deploy`
  - Manage secrets via `gcloud secrets`
  - Monitor services via `gcloud run services`
  - Build images via `gcloud builds`

## Project Structure

```
laas-platform/
├── venv/                    # Python 3.11 virtual environment
├── mcp_config.json         # MCP server configuration
├── activate_mcp.sh         # Environment activation script
├── requirements-mcp.txt    # MCP-specific dependencies
└── MCP_SETUP.md           # This documentation
```

## Configuration

### Environment Variables
- `GOOGLE_CLOUD_PROJECT`: laas-platform-1758016737
- `GOOGLE_CLOUD_REGION`: us-central1
- `MCP_CONFIG_PATH`: ./mcp_config.json

### MCP Server Configuration
The `mcp_config.json` file configures the MCP server with:
- Google Cloud project settings
- Authentication credentials path
- Service endpoints

## Next Steps

Now that MCP is installed, you can:

1. **Set up GitHub Actions** with MCP integration
2. **Deploy to Cloud Run** using MCP commands
3. **Configure monitoring** and logging
4. **Set up automated testing** with MCP

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure virtual environment is activated
   ```bash
   source venv/bin/activate
   ```

2. **Authentication Issues**: Ensure Google Cloud credentials are configured
   ```bash
   gcloud auth application-default login
   ```

3. **Permission Issues**: Check project permissions
   ```bash
   gcloud projects get-iam-policy laas-platform-1758016737
   ```

## Support

For MCP-specific issues:
- [MCP Documentation](https://modelcontextprotocol.io)
- [Google Cloud MCP Integration](https://cloud.google.com/docs/mcp)

For project-specific issues:
- Check the main README.md
- Review deployment logs
- Verify Google Cloud project configuration

