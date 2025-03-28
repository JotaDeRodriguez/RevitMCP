# Revit API Handler Design

This document outlines the design for the Revit API Handler component of the MCP integration.

## Purpose

The Revit API Handler provides access to Revit model data through an HTTP API. This allows the MCP server to query and modify Revit models without directly interfacing with the Revit API, which helps with stability and simplifies the architecture.

## Design Goals

1. **Stability** - Isolated from the MCP server to prevent crashes
2. **Performance** - Efficient data extraction and operation execution
3. **Simplicity** - Clean API design that's easy to understand and extend
4. **IronPython Compatibility** - Works with IronPython 2.7

## Core Components

The Revit API Handler consists of:

1. **HTTP Server** - Listens for API requests
2. **Request Router** - Directs requests to appropriate handlers
3. **Element Handlers** - Process element-specific operations
4. **Transaction Manager** - Manages Revit transactions
5. **Response Formatter** - Formats Revit data for consumption

## API Endpoints

### Model Information

- `GET /api/model/info` - Get basic model information
- `GET /api/model/stats` - Get model statistics

### Elements

- `GET /api/elements/{category}` - Get elements by category
- `GET /api/elements/{id}` - Get element by ID
- `GET /api/elements/{id}/parameters` - Get element parameters
- `POST /api/elements/{id}/parameters` - Set element parameters

### Views

- `GET /api/views` - Get all views
- `GET /api/views/{id}` - Get view by ID
- `POST /api/views/{id}/activate` - Activate a view

### Selection

- `GET /api/selection` - Get currently selected elements
- `POST /api/selection` - Select elements
- `DELETE /api/selection` - Clear selection

### Transactions

- `POST /api/transaction/start` - Start a transaction
- `POST /api/transaction/{id}/commit` - Commit a transaction
- `POST /api/transaction/{id}/rollback` - Rollback a transaction

## Data Flow

1. MCP server receives query requiring Revit data
2. MCP server sends HTTP request to Revit API Handler
3. Revit API Handler processes request with Revit API
4. Revit API Handler returns formatted JSON response
5. MCP server incorporates Revit data into LLM response

## Implementation Approach

### Starting the Handler

The Revit API Handler is started as part of the MCP server initialization process. It runs in a separate thread within the Revit process to ensure it has access to the Revit API.

```python
def start_revit_api_handler(port):
    """Start the Revit API Handler."""
    server = RevitAPIServer(port)
    server.start()
    return server
```

### Request Processing

Requests are processed by mapping URL patterns to handler functions:

```python
def handle_request(self, path, method, data=None):
    """Handle an API request."""
    # Route to appropriate handler
    if path.startswith('/api/model/'):
        return self.handle_model_request(path, method, data)
    elif path.startswith('/api/elements/'):
        return self.handle_element_request(path, method, data)
    elif path.startswith('/api/views/'):
        return self.handle_view_request(path, method, data)
    # etc.
```

### Element Data Extraction

Elements are extracted and converted to JSON-serializable dictionaries:

```python
def element_to_dict(element):
    """Convert a Revit element to a dictionary."""
    result = {
        'id': element.Id.IntegerValue,
        'name': getattr(element, 'Name', ''),
        'category': element.Category.Name if element.Category else '',
        'parameters': {}
    }
    
    # Add parameters
    for param in element.Parameters:
        if param.HasValue:
            result['parameters'][param.Definition.Name] = parameter_value_to_string(param)
            
    return result
```

### Transaction Management

Transactions are managed to ensure model consistency:

```python
def start_transaction(name):
    """Start a new transaction."""
    transaction = Transaction(doc, name)
    transaction.Start()
    return {
        'id': str(uuid.uuid4()),
        'name': name,
        'transaction': transaction
    }
    
def commit_transaction(transaction_id):
    """Commit a transaction."""
    transaction_info = transactions.get(transaction_id)
    if transaction_info:
        transaction_info['transaction'].Commit()
        return {'success': True}
    return {'success': False, 'error': 'Transaction not found'}
```

## IronPython Compatibility Considerations

1. Use `.format()` for string formatting (no f-strings)
2. Avoid advanced Python features not in IronPython 2.7
3. No asyncio or other modern async patterns
4. Limited exception handling capabilities
5. Consider thread safety issues with Revit API

## Error Handling

All API endpoints should use consistent error handling:

```python
try:
    # Process request
    return {'success': True, 'data': result}
except Exception as e:
    logger.error("Error: {}".format(e))
    return {'success': False, 'error': str(e)}
```

## Performance Considerations

1. Batch operations where possible
2. Minimize transaction count
3. Use filtering to reduce data size
4. Consider pagination for large result sets
5. Cache frequently accessed data

## Security Considerations

1. Only allow local connections
2. Consider adding authentication for remote access
3. Validate all input data
4. Limit operations to read-only when possible
5. Provide clear logging of all operations

## Future Extensions

1. **Webhook Support** - Allow registering webhooks for model changes
2. **WebSocket Support** - Real-time updates of model changes
3. **Bulk Operations** - Support for batch element operations
4. **Query Language** - Advanced filtering of elements
5. **Plugin System** - Extensible architecture for custom endpoints 