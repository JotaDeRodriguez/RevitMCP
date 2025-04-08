# RevitMCP Extension

## Overview
RevitMCP is a pyRevit extension that integrates the Model Context Protocol (MCP) with Autodesk Revit, enabling natural language interaction with Revit models through an AI assistant.

## Architecture
The extension follows a dual-component architecture:

1. **pyRevit Extension (IronPython 2.7)** - Revit Integration
   - Provides the UI within Revit (ribbon panel with buttons)
   - Handles interactions with the Revit API
   - Implements an RPC server to expose Revit functionality
   
2. **External MCP Server (Python 3.x)** - MCP Implementation
   - Runs as a separate process outside of Revit
   - Implements the MCP specification for AI communication
   - Connects to Anthropic Claude or other LLMs
   - Communicates with the Revit-side RPC server

## Components

### UI Components
- **Start Server**: Start/stop the MCP server
- **Settings**: Configure the MCP server and connection settings
- **Chat**: Open the chat interface for interacting with the Revit model

### Core Components
- **Revit RPC Server**: Exposes Revit functionality via a local HTTP server
- **MCP Server**: Implements the MCP specification for AI tools and resources
- **Communication Bridge**: Manages communication between components

## Requirements
- Autodesk Revit 2020 or newer
- pyRevit extension framework
- Python 3.8+ (for external MCP server)
- Anthropic API key (for Claude integration)

## Setup
See the documentation for setup and configuration instructions.

## Development
The project follows a modular architecture to allow for easy extension and maintenance. 