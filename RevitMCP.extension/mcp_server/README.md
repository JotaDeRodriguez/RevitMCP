# RevitMCP Server

This directory contains the external MCP server component of the RevitMCP extension.

## Overview

The MCP server is a Python 3.x application that implements the Model Context Protocol (MCP) specification. It runs as a separate process from Revit and communicates with the internal Revit RPC server via HTTP.

## Requirements

- Python 3.9 or higher
- Required Python packages (installed automatically via `launcher.bat`):
  - fastapi
  - uvicorn
  - requests
  - pydantic
  - anthropic
  - mcp[cli] (official MCP package)
  - httpx

## Architecture

The MCP server follows a client-server architecture:

1. **MCP Server (this component)**
   - Implements the MCP specification
   - Provides REST endpoints for communication
   - Connects to Claude via the Anthropic API
   - Uses FastMCP to expose Revit resources and tools

2. **Revit RPC Server**
   - Runs inside Revit (IronPython 2.7)
   - Exposes Revit API functionality via HTTP
   - Handles model queries and operations

## Implementation Versions

We provide two implementations of the MCP server:

### 1. `server.py` (Legacy Implementation)
- Uses the FastAPI framework with direct MCP/FastMCP integration
- Includes robust ConnectionManager for reliability
- Backward compatible with older setups

### 2. `server_mcp.py` (Modern Implementation)
- Uses the official MCP package with modern best practices
- Follows the lifespan pattern for context and state management
- Uses httpx for async HTTP requests with built-in retry logic
- Properly structures resource and tool definitions

## Components

### server.py / server_mcp.py
The main MCP server implementations that:
- Set up MCP for model context integration
- Register MCP resources and tools for Revit
- Implement a chat endpoint for Claude communication
- Handle communication with the Revit RPC server

### ConnectionManager / RevitContext
Manage connections to the Revit RPC server:
- Implement retry logic for failed connections
- Provide proper error handling and reporting
- Use connection pooling for better performance

### launcher.bat
A Windows batch script that:
- Finds the Python executable
- Installs dependencies including MCP libraries
- Launches the MCP server with specified ports
- Logs installation and startup information

## MCP Resources and Tools

The server exposes the following MCP resources and tools:

### Resources
- `revit://categories` - Get all available Revit categories
- `revit://elements/{category}` - Get elements of a specific category from the Revit model

### Tools
- `get_revit_categories` - Get all available Revit categories
- `get_category_elements` - Get elements of a specific category
- `get_element_parameter` - Get a specific parameter value for an element
- `select_elements` - Select elements in the Revit UI by their IDs
- `create_wall` - Create a wall with specified parameters
- `create_line_based_element` - Create a line-based element (walls, beams, etc.)

## Communication

- MCP Server Port (default: 9876): Used for MCP communication with Claude
- Revit RPC Port (default: 9877): Used for communication with the Revit RPC server

The server uses HTTP/JSON for all communication with robust error handling.

## Error Handling

The server implements a comprehensive error handling strategy:
- `ConnectionError` - When unable to connect to the Revit RPC server
- `RPCError` - When there's an error in the RPC response
- `RevitAPIError` - When there's an error in the Revit API
- `MCRError` - Base class for all MCP-related errors

## Usage

The server is designed to be launched from the pyRevit extension's "Start Server" button. Manual launching is possible:

```
# Launch the legacy implementation
launcher.bat <mcp_port> <revit_port>

# Launch the modern implementation
python server_mcp.py --mcp-port <mcp_port> --revit-port <revit_port>
```

Installation logs are stored in the `logs` directory.

## MCP Implementation Details

The modern implementation follows the official MCP best practices:

### Lifespan Management
Uses the `asynccontextmanager` pattern to properly manage resources throughout the server lifecycle:

```python
@asynccontextmanager
async def revit_lifespan(server: FastMCP) -> AsyncIterator[RevitContext]:
    # Initialize resources
    try:
        yield context
    finally:
        # Clean up resources
```

### Type-Safe Context
Provides a strongly-typed context for accessing shared state:

```python
class RevitContext:
    def __init__(self, client: httpx.AsyncClient, api_key: Optional[str] = None):
        # Initialize with type hints
```

### Modern HTTP Client
Uses httpx for async HTTP requests with built-in retry logic:

```python
client = httpx.AsyncClient(
    limits=limits,
    timeout=timeout,
    transport=transport
)
```

### Resource and Tool Definitions
Clean, well-documented resource and tool definitions with proper typing:

```python
@mcp.resource("revit://elements/{category}")
async def get_elements(category: str, ctx: Context) -> List[Dict[str, Any]]:
    """Get elements of a specified category from the Revit model."""
``` 