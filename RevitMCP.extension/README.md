# RevitMCP - Model Cognition Platform for Revit

RevitMCP is a PyRevit extension that integrates Revit with Large Language Models (LLMs) to enable natural language interaction with your building information models.

## Overview

RevitMCP provides a bridge between Revit and LLMs, allowing users to query model information using natural language. The platform leverages a hybrid architecture with:

1. A client-side Python module running in Revit/PyRevit for direct Revit API access
2. A server-side Python component that manages LLM interaction and handles requests

## Features

- **Chat Interface:** Ask questions about your Revit model in natural language
- **Server Management:** Start and stop the MCP server directly from Revit
- **Settings Management:** Configure server ports, API keys, and model selection
- **Revit API Integration:** Extract model information directly through the Revit API
- **Fallback Responses:** Continue working even when server connectivity is limited

## Components

- **Chat Interface:** Dialog for interacting with the MCP system
- **Test Interface:** Lightweight utility for testing server connectivity and responses
- **Server Control:** Manage the MCP server lifecycle
- **Settings:** Configure MCP server parameters
- **Server and Connector Libraries:** Core functionality for server and Revit API interaction

## Getting Started

1. Install the RevitMCP extension in PyRevit
2. Launch Revit and open a model
3. Use the "Server_Control" button in the MCP panel to start the server
4. Use the "Chat_Interface" or "Test_Interface" to interact with your model
5. Configure connection settings using the "Settings" button

## Technical Architecture

RevitMCP follows a hybrid architecture pattern:

1. **Revit/PyRevit (IronPython 2.7):** Handles UI and direct Revit API access
2. **External Python Server (Python 3.x):** Manages LLM API connections and request processing

This architecture overcomes limitations of IronPython 2.7 in Revit while maintaining direct API access.

## Development

The project is organized as follows:

```
RevitMCP.extension/
├── RevitMCP.tab/
│   └── MCP.panel/
│       ├── Chat_Interface.pushbutton/
│       ├── Test_Interface.pushbutton/
│       ├── Server_Control.pushbutton/
│       ├── Settings.pushbutton/
│       ├── lib/
│       │   ├── mcp_connector.py
│       │   └── server_registry.py
│       ├── server/
│       │   ├── dummy_server.py
│       │   └── server_launcher.bat
│       └── docs/
│           ├── revit_api_design.md
│           └── ...
└── README.md
```

## Requirements

- PyRevit 4.8+
- Revit 2020+
- Python 3.8+ (for the server component)
- Internet connection for LLM API access (unless using local models)

## Future Development

- WebSocket support for real-time updates
- Integration with more LLM providers
- Expanded Revit API coverage
- Improved visualization of results
- Custom training on AEC-specific knowledge

## License

This project is licensed under the MIT License. 