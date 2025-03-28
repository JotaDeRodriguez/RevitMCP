# MCP Server Control

This PyRevit button provides an interface for managing the Machine Conversation Protocol (MCP) server.

## Features

- Start and stop the MCP server
- View server status and configuration
- Access server logs
- Monitor server health

## Usage

1. Click the Server Control button in the MCP panel
2. Use the provided interface to:
   - Start the MCP server (if not running)
   - Stop the MCP server (if running)
   - View server logs
   - Check server status and configuration

## Server Information

The MCP server runs as a separate Python process and manages communication between Revit and Large Language Models (LLMs). It provides:

- HTTP endpoints for processing language queries
- A bridge between the Revit API and language models
- Formatted responses for display in the chat interface

## Troubleshooting

### Server Won't Start

- Ensure Python 3.7+ is installed and available
- Check if the server ports (default: 9876 and 9877) are available
- Verify you have sufficient permissions to start processes
- Check the server logs for detailed error messages

### Server Crashes or is Unreliable

- Ensure you have the latest version of all dependencies
- Check for network or firewall issues
- Verify your API keys are correctly configured
- Examine server logs for error patterns

## Server Configuration

The server uses the following default ports:

- **MCP Port**: 9876 (for LLM API communication)
- **Revit Port**: 9877 (for Revit API communication)

These settings can be modified in the configuration if needed.

## Advanced: Manual Server Control

If the UI-based server control doesn't work, you can manually start the server by:

1. Opening a command prompt
2. Navigating to the server directory
3. Running: `python dummy_server.py 9876 9877`

Replace the port numbers with your desired values if different from defaults. 