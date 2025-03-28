# MCP Chat Interface

This PyRevit button provides a rich chat interface for interacting with your Revit model through the Machine Conversation Protocol (MCP).

## Features

- Modern, intuitive chat interface
- Real-time communication with the MCP server
- Persistent chat history
- Server status monitoring
- Copy and paste support
- Markdown rendering for responses (coming soon)
- Element highlighting (coming soon)

## Usage

1. Click the Chat Interface button in the MCP panel
2. If the MCP server is not running, you'll be prompted to start it
3. Type your question in the input box and press Enter or click Send
4. View the response from the MCP server in the chat history

## Examples

You can ask questions about your Revit model, such as:

- "How many walls are in this model?"
- "Show me all doors with a height greater than 7 feet"
- "What is the total area of floors in the model?"
- "List all windows in the east facade"

## Troubleshooting

- If the server doesn't respond, check the Server Control panel to ensure it's running
- If responses are slow, ensure your model is not too large or complex
- If you encounter errors, check the PyRevit logs for details

## Requirements

- PyRevit 4.7 or later
- Python 3.7 or later (for the MCP server component)
- Network connectivity between the Revit client and the MCP server 