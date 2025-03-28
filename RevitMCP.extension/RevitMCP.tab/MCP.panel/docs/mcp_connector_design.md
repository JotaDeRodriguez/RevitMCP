# MCP Connector Design

This document outlines the design for the MCP Connector component, which serves as the bridge between various parts of the Revit MCP integration.

## Purpose

The MCP Connector provides a unified interface for:
- Managing the MCP Server lifecycle
- Handling communication between PyRevit and the MCP Server
- Managing settings and configuration
- Coordinating interactions between components

## Design Goals

1. **Simplicity** - Clean, understandable API
2. **Reliability** - Robust error handling and recovery
3. **Compatibility** - Works in both IronPython and standard Python environments
4. **Configurability** - Easy to configure and customize
5. **Extensibility** - Simple to extend with new features

## Core Components

The MCP Connector consists of:

1. **Server Manager** - Controls MCP Server lifecycle
2. **Client API** - Interface for sending requests to MCP Server
3. **Settings Manager** - Handles configuration and persistence
4. **Coordination Service** - Facilitates inter-component communication

## Component Details

### Server Manager

The Server Manager handles the MCP Server lifecycle:

- **Server Start** - Launches the MCP Server process
- **Server Stop** - Gracefully shuts down the MCP Server
- **Status Check** - Verifies if server is running
- **Process Management** - Monitors server process health
- **Logging** - Captures and stores server logs

#### Implementation Approach

```python
def start_server(self, port=9876, revit_port=9877):
    """Start the MCP server."""
    try:
        # Check if server is already running
        if self.is_server_running(port):
            logger.info("Server already running on port {}".format(port))
            return True
            
        # Get path to server script
        server_script = os.path.join(
            os.path.dirname(__file__),
            "server",
            "dummy_server.py"
        )
        
        # Start server process
        process = subprocess.Popen(
            [sys.executable, server_script, str(port), str(revit_port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        # Store process for later management
        self.server_process = process
        
        # Wait for server to start
        time.sleep(1)
        
        # Verify server started
        if self.is_server_running(port):
            logger.info("Server started on port {}".format(port))
            return True
        else:
            logger.error("Server failed to start")
            return False
    except Exception as e:
        logger.error("Error starting server: {}".format(str(e)))
        return False
```

### Client API

The Client API provides a simple interface for communicating with the MCP Server:

- **Request Sending** - Sends queries to MCP Server
- **Response Handling** - Processes and formats server responses
- **Error Handling** - Manages communication errors
- **Authentication** - Handles authentication if needed
- **Retry Logic** - Implements retries for transient failures

#### Implementation Approach

```python
def query(self, message, model=None):
    """Send a query to the MCP server."""
    try:
        # Check if server is running
        if not self.is_server_running():
            if not self.start_server():
                raise Exception("Failed to start server")
        
        # Create request payload
        payload = {
            "messages": [
                {"role": "user", "content": message}
            ]
        }
        
        # Add model if specified
        if model:
            payload["model"] = model
            
        # Convert payload to JSON
        data = json.dumps(payload)
        
        # Create HTTP request
        url = "{}/api/v1/generate".format(self.base_url)
        headers = {"Content-Type": "application/json"}
        
        # Send request
        response = self.http_post(url, data, headers)
        
        # Parse response
        if response.status_code == 200:
            return json.loads(response.content)
        else:
            logger.error("Error from server: {}".format(response.status_code))
            return None
    except Exception as e:
        logger.error("Error querying server: {}".format(str(e)))
        return None
```

### Settings Manager

The Settings Manager handles configuration and persistence:

- **Load Settings** - Retrieves settings from storage
- **Save Settings** - Persists settings to storage
- **Validate Settings** - Ensures settings are valid
- **Default Settings** - Provides sensible defaults
- **Migration** - Handles settings upgrades

#### Implementation Approach

```python
def load_settings(self):
    """Load settings from storage."""
    try:
        # Get PyRevit config
        config = script.get_config()
        
        # Load settings with defaults
        self.settings = {
            "mcp_port": config.get_option("mcp_port", 9876),
            "revit_port": config.get_option("revit_port", 9877),
            "api_key": config.get_option("api_key", ""),
            "model": config.get_option("model", "claude-3-haiku-20240307"),
            "log_level": config.get_option("log_level", "INFO")
        }
        
        return self.settings
    except Exception as e:
        logger.error("Error loading settings: {}".format(str(e)))
        # Return defaults
        return {
            "mcp_port": 9876,
            "revit_port": 9877,
            "api_key": "",
            "model": "claude-3-haiku-20240307",
            "log_level": "INFO"
        }
```

### Coordination Service

The Coordination Service facilitates inter-component communication:

- **Event Management** - Handles events between components
- **State Sharing** - Manages shared state
- **Status Reporting** - Consolidates status information
- **Error Propagation** - Ensures consistent error handling
- **Logging Coordination** - Centralizes logging

#### Implementation Approach

```python
def register_event_handler(self, event_name, handler):
    """Register a handler for an event."""
    if event_name not in self.event_handlers:
        self.event_handlers[event_name] = []
    self.event_handlers[event_name].append(handler)
    
def trigger_event(self, event_name, event_data=None):
    """Trigger an event with optional data."""
    if event_name in self.event_handlers:
        for handler in self.event_handlers[event_name]:
            try:
                handler(event_data)
            except Exception as e:
                logger.error("Error in event handler: {}".format(str(e)))
```

## Integration Points

### With PyRevit UI

The connector integrates with the PyRevit UI through:

```python
def connect_to_ui(self, ui_handler):
    """Connect to the PyRevit UI handler."""
    # Register for UI events
    self.register_event_handler("ui_query", self.handle_ui_query)
    self.register_event_handler("ui_server_start", self.start_server)
    self.register_event_handler("ui_server_stop", self.stop_server)
    
    # Register to provide status updates to UI
    def status_update_handler(status_data):
        ui_handler.update_status(status_data)
    self.register_event_handler("status_update", status_update_handler)
```

### With MCP Server

The connector integrates with the MCP Server through:

```python
def connect_to_server(self):
    """Connect to the MCP server."""
    # Start server if not running
    if not self.is_server_running():
        self.start_server()
    
    # Test connection
    try:
        response = self.http_get("{}/api/v1/resources".format(self.base_url))
        if response.status_code == 200:
            self.trigger_event("status_update", {
                "type": "server",
                "status": "connected"
            })
            return True
        else:
            return False
    except:
        return False
```

## Error Handling

The connector implements comprehensive error handling:

```python
def safe_operation(func):
    """Decorator for safe operation with error handling."""
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            # Log error
            logger.error(
                "Error in {}: {}".format(func.__name__, str(e))
            )
            # Trigger error event
            self.trigger_event("error", {
                "source": "connector",
                "operation": func.__name__,
                "error": str(e)
            })
            # Return error indicator
            return None
    return wrapper
```

## IronPython Compatibility

To ensure compatibility with IronPython 2.7:

1. **String Formatting** - Use `.format()` instead of f-strings
2. **HTTP Requests** - Use compatible HTTP client library
3. **Process Management** - Use compatible process spawning
4. **Exception Handling** - Handle IronPython-specific exceptions
5. **Module Imports** - Only use available modules

## Security Considerations

1. **API Key Handling** - Secure storage of API keys
2. **Local Only** - Only connect to localhost servers
3. **Input Validation** - Validate all inputs before sending
4. **Error Messages** - Avoid exposing sensitive information
5. **Secure Defaults** - Secure by default configuration

## Performance Considerations

1. **Connection Pooling** - Reuse connections when possible
2. **Request Caching** - Cache frequent requests
3. **Lazy Initialization** - Initialize components on demand
4. **Resource Cleanup** - Properly dispose of resources
5. **Minimal Dependencies** - Limit external dependencies

## Future Extensions

1. **Authentication** - Support for authenticated connections
2. **Encryption** - Support for encrypted communication
3. **Streaming** - Support for streaming responses
4. **Metrics** - Capture and report performance metrics
5. **Plugins** - Support for connector plugins 