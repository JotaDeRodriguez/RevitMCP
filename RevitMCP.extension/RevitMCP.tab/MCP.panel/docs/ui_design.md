# User Interface Design

This document outlines the design for the User Interface components of the Revit MCP integration.

## Purpose

The User Interface provides Revit users with an intuitive way to interact with the MCP system, enabling natural language queries about models and visualization of responses.

## Design Goals

1. **Simplicity** - Easy to understand and use
2. **Stability** - Robust operation within Revit
3. **Responsiveness** - Quick feedback on user actions
4. **Consistency** - Familiar PyRevit extension patterns
5. **Compatibility** - Works within IronPython constraints

## Core Components

The UI consists of:

1. **Chat Interface** - For entering queries and viewing responses
2. **Server Control** - For starting/stopping the MCP server
3. **Settings Panel** - For configuring the MCP system
4. **Status Indicators** - For showing server and connection status

## Component Details

### Chat Interface

The Chat Interface is the primary user touchpoint:

- **Input Area** - Text box for entering natural language queries
- **Chat History** - Display of previous queries and responses
- **Send Button** - Submits queries to the MCP server
- **Progress Indicator** - Shows when a response is being generated
- **Element Highlights** - Visual highlights of referenced elements

#### Implementation Approach

```python
def create_chat_interface(self):
    """Create the chat interface component."""
    # Create a simple form using WPF
    form = ui.forms.WPFWindow(
        "Chat.xaml",
        title="Revit MCP Chat"
    )
    
    # Set up the chat history display
    chat_history = form.chat_history
    
    # Set up the input box
    input_box = form.input_box
    send_button = form.send_button
    
    # Wire up events
    send_button.Click += self.send_query
    
    return form
```

### Server Control

The Server Control manages the MCP server lifecycle:

- **Start Button** - Starts the MCP server
- **Stop Button** - Stops the MCP server
- **Status Indicator** - Shows if server is running
- **Port Setting** - Configures server port
- **Server Logs** - Shows recent server activity

#### Implementation Approach

```python
def create_server_control(self):
    """Create the server control component."""
    # Create controls using standard PyRevit forms
    server_form = ui.forms.alert(
        title="MCP Server Control",
        options=[
            "Start Server",
            "Stop Server",
            "View Logs",
            "Close"
        ]
    )
    
    return server_form
```

### Settings Panel

The Settings Panel allows configuration of the MCP system:

- **API Keys** - For configuring LLM service access
- **Server Settings** - For configuring server behavior
- **Model Selection** - For choosing which LLM to use
- **UI Preferences** - For customizing the UI
- **Advanced Options** - For expert users

#### Implementation Approach

```python
def create_settings_panel(self):
    """Create the settings panel."""
    # Use PyRevit's built-in configuration system
    settings = script.get_config()
    
    # Create a form to edit settings
    form = ui.forms.ConfigurationWindow(
        settings,
        title="MCP Settings"
    )
    
    return form
```

### Status Indicators

Status Indicators provide real-time feedback:

- **Server Status** - Shows if server is running
- **Connection Status** - Shows if connected to LLM API
- **Process Indicator** - Shows when processing a query
- **Error Notifications** - Shows if something goes wrong

#### Implementation Approach

```python
def update_status(self, status_type, message):
    """Update status indicators."""
    if status_type == "server":
        self.server_status.Text = message
        if "Running" in message:
            self.server_status.Foreground = Brushes.Green
        else:
            self.server_status.Foreground = Brushes.Red
    elif status_type == "connection":
        # Update connection status
        pass
    elif status_type == "error":
        # Show error notification
        pass
```

## User Flows

### Starting a Conversation

1. User opens the Chat Interface
2. System checks if server is running
3. If not running, system starts server
4. User enters a query about the model
5. System shows processing indicator
6. System displays response
7. Elements mentioned in response are highlighted

### Configuring Settings

1. User opens Settings Panel
2. User enters API key for LLM service
3. User selects preferred model
4. User saves settings
5. System validates and stores settings

## IronPython Compatibility

To ensure compatibility with IronPython 2.7:

1. **Simple UI Components** - Use basic WPF controls
2. **Limited Threading** - Minimal use of threading
3. **Progress Updates** - Use timer-based updates instead of async
4. **Error Handling** - Capture and log IronPython-specific errors
5. **String Formatting** - Use `.format()` instead of f-strings

## Error Handling

The UI implements user-friendly error handling:

```python
try:
    # Send query to server
    response = self.send_query_to_server(query)
    self.display_response(response)
except Exception as e:
    # Show user-friendly error
    ui.forms.alert(
        "Unable to process your query. Please try again.",
        title="Error"
    )
    # Log detailed error
    logger.error("Error: {}".format(str(e)))
```

## Visual Design

The UI follows these design principles:

1. **Clean Layout** - Minimal, focused interface
2. **Consistent Styling** - Match Revit's visual style
3. **Clear Feedback** - Obvious status indicators
4. **Accessibility** - High contrast, readable text
5. **Compact Design** - Minimal screen space usage

## Performance Considerations

1. **Lazy Loading** - Load components only when needed
2. **Throttling** - Limit frequency of updates
3. **Minimal Refreshes** - Update only changed parts of UI
4. **Background Processing** - Keep UI responsive
5. **Memory Management** - Release resources promptly

## Future Extensions

1. **Element Selection** - Select elements mentioned in chat
2. **Context Menu** - Right-click options for elements
3. **Image Support** - Display images in chat
4. **Voice Input** - Support for voice queries
5. **Multi-window Support** - Detachable chat window 