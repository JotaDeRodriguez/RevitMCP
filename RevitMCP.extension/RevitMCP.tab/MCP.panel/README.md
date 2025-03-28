# Revit MCP Integration

This PyRevit extension connects Revit to the Model-Code-Program (MCP) paradigm, allowing large language models to interact with your Revit models.

## Installation

1. Install [PyRevit](https://github.com/eirannejad/pyRevit/releases) if you haven't already
2. Download or clone this repository
3. Copy the `RevitMCP.extension` folder to your PyRevit extensions folder (typically `%APPDATA%\pyRevit\extensions`)
4. Restart Revit or reload PyRevit

## Features

- **Start/Stop MCP Server**: Control the MCP server that handles communication between Revit and LLMs
- **Settings**: Configure port numbers, Python path, and API keys
- **Test Interface**: Simple UI for testing queries against your Revit model

## Getting Started

1. Click the **Test** button to verify that the extension is working correctly
2. Open the **Settings** button to configure your ports and API key
3. Click **Start MCP Server** to start the server
4. Use the **Test Interface** to try out some queries

## Requirements

- Revit 2021 or newer
- PyRevit 4.8 or newer
- Python 2.7 (via IronPython, included with PyRevit)

## Development

The extension consists of several key components:

- `Start_MCP_Server.pushbutton`: Controls the MCP server
- `Settings.pushbutton`: Configures the extension
- `Test_Interface.pushbutton`: Provides a simple UI for testing
- `lib/mcp_connector.py`: Core module for MCP integration
- `server/revit_api_server.py`: HTTP server for Revit API access

## Troubleshooting

If you encounter issues:

1. Check the PyRevit console for error messages
2. Verify that all required files are in the correct directories
3. Make sure ports aren't being used by other applications
4. Try stopping and restarting the MCP server

## License

This project is open-source and available under the MIT License.

## Contact

For questions or feedback, please open an issue on the GitHub repository. 