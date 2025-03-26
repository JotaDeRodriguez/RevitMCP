# Revit MCP Integration

A Model Context Protocol (MCP) integration for Autodesk Revit 2024.3, enabling AI assistants like Claude to interact directly with Revit models through natural language.

## Overview

This integration allows Large Language Models (LLMs) to:
- Query information from Revit models
- Create and modify elements
- Perform complex operations through a standardized interface

The implementation uses the Model Context Protocol (MCP), an open standard developed by Anthropic that defines how AI models can connect to external tools and data sources.

## Requirements

- Autodesk Revit 2024.3 or newer
- Python 3.13 (must be installed and available in PATH)
- PyRevit (latest version)
- MCP Python SDK (`pip install mcp[cli]`)

## Installation

1. Install Python 3.13 from [python.org](https://www.python.org/downloads/)
2. Install required Python packages:
   ```
   pip install mcp[cli] httpx
   ```
3. Install the latest version of PyRevit for Revit 2024
4. Copy the `RevitMCP.extension` folder to your PyRevit extensions folder:
   - Typically located at: `%APPDATA%\pyRevit\extensions`
5. Reload PyRevit from the Revit ribbon

## Getting Started

1. Open Revit and your model
2. Go to the "RevitMCP" tab in the Revit ribbon
3. Click "Start MCP Server" to launch the MCP server
4. Open Claude Desktop or other MCP-compatible clients
5. Configure the MCP client to connect to the server
6. Start asking questions or giving commands about your Revit model!

## Using the Test Interface

If you don't have Claude Desktop or another MCP client, you can use the built-in test interface:

1. Open Revit and your model
2. Go to the "RevitMCP" tab in the Revit ribbon
3. Click "Test Interface" to open the chat interface
4. The interface will automatically try to connect to a running MCP server
5. If no server is running, it will try to start one
6. You can select an example query from the dropdown or type your own
7. Click "Send" or press Enter to submit your query
8. The response will appear in the conversation window

This test interface allows you to:

- Query Revit model information
- List elements by category (walls, doors, rooms, etc.)
- Create new elements
- Get and set parameter values
- Test the MCP integration without needing external tools

## Claude Desktop Integration

To connect Claude Desktop to your Revit MCP server:

1. Edit your Claude Desktop configuration file:
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. Add the following configuration:
   ```json
   {
     "mcpServers": {
       "revit": {
         "command": "python",
         "args": ["C:/path/to/revit_mcp_server.py"]
       }
     }
   }
   ```

3. Replace `C:/path/to/revit_mcp_server.py` with the actual path to the `revit_mcp_server.py` file

## Features

The integration exposes the following capabilities to the MCP client:

### Resources
- `revit://model/info` - Basic model information
- `revit://elements/{category}` - Elements of a specific category

### Tools
- `get_revit_info()` - Get basic model information
- `find_elements(category, filter_params)` - Find elements by category
- `get_element_parameters(element_id)` - Get all parameters for an element
- `set_element_parameter(element_id, parameter_name, value)` - Set a parameter value
- `get_views()` - Get all views in the document
- `create_wall(start_point, end_point, height, wall_type_name)` - Create a wall
- `start_transaction(name)` - Start a transaction
- `commit_transaction(transaction_id)` - Commit a transaction

## Example Prompts

Try these prompts with Claude when connected to your Revit model:

- "What walls are in the current model?"
- "Show me all rooms on Level 1"
- "Create a wall at coordinates (0,0) to (10,0) with height 10 feet"
- "What is the fire rating of the selected wall?"
- "List all doors in the model grouped by type"

## Troubleshooting

- **Server won't start**: Ensure Python 3.13 is installed and in your PATH
- **Connection errors**: Check firewall settings for ports 9876 and 9877
- **Missing modules**: Run `pip install mcp[cli] httpx` to install required packages
- **PyRevit errors**: Make sure you're using the latest PyRevit version compatible with Revit 2024

## License

This project is released under the MIT License.

## Acknowledgments

- Anthropic for developing the Model Context Protocol
- The PyRevit team for their excellent Revit API wrapper 