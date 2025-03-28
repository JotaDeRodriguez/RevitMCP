# MCP Server Design

This document outlines the design for the MCP Server component, which serves as the core of the Revit MCP integration.

## Purpose

The MCP Server is a lightweight HTTP server that acts as a bridge between:
- The Revit user interface (via PyRevit)
- Large Language Model APIs (Claude, GPT, etc.)
- The Revit API (via the Revit API Handler)

It processes natural language queries about Revit models and returns intelligent responses.

## Design Goals

1. **Reliability** - Stable operation with clean error handling
2. **Performance** - Responsive even with large model data
3. **Flexibility** - Support for multiple LLM providers
4. **Compatibility** - Works with both modern Python and IronPython
5. **Extensibility** - Easy to add new capabilities

## Core Components

The MCP Server consists of:

1. **HTTP Server** - Handles incoming requests
2. **Request Router** - Directs requests to appropriate handlers
3. **LLM Clients** - Interfaces with language model APIs
4. **Revit API Client** - Communicates with the Revit API Handler
5. **Response Formatter** - Structures responses for the UI

## API Endpoints

### Resources

- `GET /api/v1/resources` - List available resources/capabilities

### Generation

- `POST /api/v1/generate` - Generate a response to a query
- `POST /api/v1/generate_stream` - Stream a response (future)

### Administration

- `GET /shutdown` - Gracefully shut down the server

## Request/Response Format

### Generate Request

```json
{
  "messages": [
    {"role": "user", "content": "Tell me about the walls in my model"}
  ],
  "stream": false,
  "model": "claude-3-haiku-20240307"
}
```

### Generate Response

```json
{
  "id": "gen-123",
  "model": "claude-3-haiku-20240307",
  "created": 1681234567,
  "content": "I found 42 walls in your model: 28 Basic Walls and 14 Exterior Walls..."
}
```

## Implementation Approach

### Server Initialization

The server is started as a separate process to ensure stability:

```python
def start_server(port, revit_port):
    """Start the MCP server."""
    server = MCPServer(port, revit_port)
    server.start()
    return server
```

### Request Handling

Requests are processed by mapping URL patterns to handler functions:

```python
def handle_request(self, method, path, body=None):
    """Handle an HTTP request."""
    # Route to appropriate handler
    if path == '/api/v1/resources' and method == 'GET':
        return self.handle_resources()
    elif path == '/api/v1/generate' and method == 'POST':
        return self.handle_generate(body)
    elif path == '/shutdown' and method == 'GET':
        return self.handle_shutdown()
    else:
        return self.handle_not_found()
```

### Query Processing

Queries are processed using a chain of responsibility:

1. Parse the query
2. Detect Revit-specific intents
3. Gather relevant Revit data
4. Generate a response using the LLM
5. Format and return the response

```python
def process_query(self, query):
    """Process a natural language query."""
    # Parse query
    intent = self.detect_intent(query)
    
    # Gather Revit data if needed
    revit_data = None
    if intent.requires_revit_data:
        revit_data = self.gather_revit_data(intent)
    
    # Generate response
    response = self.generate_response(query, intent, revit_data)
    
    return response
```

### LLM Integration

The server integrates with LLMs through API clients:

```python
def get_llm_client(self, model_name):
    """Get an LLM client for the specified model."""
    if "claude" in model_name:
        return self.get_anthropic_client()
    elif "gpt" in model_name:
        return self.get_openai_client()
    else:
        return self.get_default_client()
```

### Revit API Integration

The server communicates with the Revit API Handler through HTTP:

```python
def get_revit_data(self, endpoint, params=None):
    """Get data from the Revit API Handler."""
    revit_client = self.revit_client
    url = f"/api/{endpoint}"
    response = revit_client.get(url, params=params)
    return response.json()
```

## Error Handling

The server implements comprehensive error handling:

```python
try:
    # Process request
    response = self.process_query(query)
    return self.format_success_response(response)
except RevitAPIError as e:
    return self.format_error_response("Revit API error", e)
except LLMAPIError as e:
    return self.format_error_response("LLM API error", e)
except Exception as e:
    return self.format_error_response("Unexpected error", e)
```

## Security Considerations

1. **Local Only** - Only accepts connections from localhost
2. **Input Validation** - Validates all input before processing
3. **API Key Security** - Careful handling of LLM API keys
4. **Data Protection** - No persistent storage of sensitive data
5. **Limited Scope** - Restricted commands and transactions

## Performance Optimizations

1. **Caching** - Cache common responses
2. **Batching** - Batch Revit API requests
3. **Async Processing** - Use async where appropriate
4. **Streaming** - Stream large responses

## Deployment Considerations

1. **Startup** - Started on demand from PyRevit
2. **Shutdown** - Gracefully shut down on command or Revit close
3. **Updates** - Check for updates on startup
4. **Logging** - Comprehensive logging for debugging
5. **Configuration** - User-configurable settings

## Future Extensions

1. **Multi-user Support** - Support for multiple Revit users
2. **Federated Models** - Support for linked models
3. **History** - Persistent chat history
4. **File Upload** - Support for file uploads
5. **Drawing Analysis** - Support for analyzing drawings 