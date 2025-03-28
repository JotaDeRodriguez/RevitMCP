# MCP Settings

The Settings button provides an interface to configure the MCP server parameters.

## Features

- Configure MCP server port (default: 9876)
- Configure Revit API port (default: 9877)
- Set API key for LLM services
- Specify LLM model to use
- Toggle auto-start server option

## Usage

1. Click the Settings button in the MCP panel
2. Adjust the settings as needed
3. Click 'Save' to apply changes
4. If the server is currently running, you may need to restart it for changes to take effect

## Configuration Options

- **MCP Port**: The port used for communication between the MCP server and client (default: 9876)
- **Revit Port**: The port used for communication between the MCP server and Revit API (default: 9877)
- **API Key**: Your API key for the LLM service
- **Model**: The LLM model to use (e.g., "gpt-4")
- **Auto-start server**: When enabled, the server will start automatically when needed

## Troubleshooting

- If you encounter connection issues, try changing the port numbers
- Make sure the ports you specify are not in use by other applications
- Ensure your API key is valid and has access to the specified model
- If changes don't seem to take effect, restart Revit and try again 