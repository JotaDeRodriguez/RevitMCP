"""
RevitMCP Server
Implements the Model Context Protocol (MCP) for Revit.
"""

import os
import sys
import json
import argparse
import signal
import time
import traceback
import datetime
import logging
import inspect
from typing import List, Dict, Any, Optional, Union, Callable
import threading

# Define error classes regardless of whether MCP is available
class MCRError(Exception):
    """Base error class for Revit MCR errors"""
    pass

class ConnectionError(MCRError):
    """Error connecting to Revit RPC server"""
    pass

class RPCError(MCRError):
    """Error when Revit RPC call fails"""
    pass

class RevitAPIError(MCRError):
    """Error in Revit API operations"""
    pass

class InvalidRequestError(Exception):
    """Error class for invalid MCP requests"""
    pass

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "server_log.txt")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RevitMCP")

# Import requests first to use in the ConnectionManager
try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError as e:
    logger.error(f"Missing requests dependency: {e}")
    logger.error("Please install requests using: pip install requests")
    sys.exit(1)

class RevitConnectionManager:
    """
    Manages connections to the Revit RPC server with proper error handling
    and retry logic.
    """
    
    def __init__(self, host="localhost", port=9877):
        """Initialize the connection manager."""
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.session = None
        self.last_connection_attempt = 0
        self.connection_timeout = 30  # seconds
        self.retry_cooldown = 5  # seconds
        self.max_retries = 3
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize requests session with retry logic."""
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=0.5,
            status_forcelist=[408, 429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def close(self):
        """Close the session."""
        if self.session:
            self.session.close()
            self.session = None
    
    def call_revit_rpc(self, endpoint: str, data: Dict[str, Any], retry_count=0) -> Any:
        """
        Call the Revit RPC server with proper error handling and retries.
        
        Args:
            endpoint: API endpoint to call
            data: JSON payload to send
            retry_count: Current retry attempt (used internally)
            
        Returns:
            Response data from Revit server
            
        Raises:
            ConnectionError: If cannot connect to the Revit server
            RPCError: If the Revit server returns an error
        """
        if retry_count >= self.max_retries:
            raise ConnectionError(f"Failed to connect to Revit RPC server after {self.max_retries} attempts")
            
        current_time = time.time()
        if retry_count > 0 and current_time - self.last_connection_attempt < self.retry_cooldown:
            time.sleep(self.retry_cooldown - (current_time - self.last_connection_attempt))
            
        self.last_connection_attempt = time.time()
        
        try:
            # Make a POST request to the Revit RPC server
            response = self.session.post(
                f"{self.base_url}/{endpoint}",
                json=data,
                timeout=self.connection_timeout
            )
            
            # Check if the response was successful
            response.raise_for_status()
            
            # Parse and validate the response
            response_data = response.json()
            
            if response_data.get("status") == "error":
                raise RPCError(f"Revit RPC error: {response_data.get('message', 'Unknown error')}")
                
            return response_data.get("data")
            
        except requests.exceptions.HTTPError as e:
            logger.warning(f"HTTP error: {e}. Attempt {retry_count+1}/{self.max_retries}")
            if retry_count < self.max_retries - 1:
                return self.call_revit_rpc(endpoint, data, retry_count + 1)
            raise ConnectionError(f"HTTP error communicating with Revit: {e}")
            
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error: {e}. Attempt {retry_count+1}/{self.max_retries}")
            if retry_count < self.max_retries - 1:
                return self.call_revit_rpc(endpoint, data, retry_count + 1)
            raise ConnectionError(f"Failed to connect to Revit RPC server: {e}")
            
        except requests.exceptions.Timeout as e:
            logger.warning(f"Timeout error: {e}. Attempt {retry_count+1}/{self.max_retries}")
            if retry_count < self.max_retries - 1:
                return self.call_revit_rpc(endpoint, data, retry_count + 1)
            raise ConnectionError(f"Timeout connecting to Revit RPC server: {e}")
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error: {e}. Attempt {retry_count+1}/{self.max_retries}")
            if retry_count < self.max_retries - 1:
                return self.call_revit_rpc(endpoint, data, retry_count + 1)
            raise ConnectionError(f"Error communicating with Revit: {e}")
            
        except Exception as e:
            logger.error(f"Unexpected error calling Revit RPC ({endpoint}): {e}")
            logger.error(traceback.format_exc())
            raise RPCError(f"Unexpected error communicating with Revit: {str(e)}")
    
    def ping(self) -> bool:
        """
        Check if the Revit RPC server is available.
        
        Returns:
            True if server is available, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/ping", timeout=5)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.debug(f"Ping failed: {e}")
            return False

# Try to import required libraries
try:
    from fastapi import FastAPI, HTTPException, Depends, Request, Response
    from fastapi.responses import JSONResponse, HTMLResponse
    from fastapi.middleware.cors import CORSMiddleware  # Import CORS middleware
    import uvicorn
    from pydantic import BaseModel, Field
except ImportError as e:
    logger.error(f"Missing required dependency: {e}")
    logger.error("Please install required packages using: pip install -r requirements.txt")
    sys.exit(1)

# Try to import MCP libraries
MCP_AVAILABLE = False
try:
    import mcp
    logger.info("MCP package imported successfully")
    MCP_AVAILABLE = True
except ImportError as e:
    logger.warning(f"MCP package not available: {e}")
    MCP_AVAILABLE = False

if not MCP_AVAILABLE:
    logger.warning("Falling back to basic FastAPI server without MCP functionality")

# Try to import Anthropic SDK
ANTHROPIC_AVAILABLE = True
try:
    import anthropic
except ImportError as e:
    logger.warning(f"Anthropic SDK not available: {e}")
    logger.warning("Claude integration will be limited")
    ANTHROPIC_AVAILABLE = False

# Define Pydantic models for parameter validation
class Point3D(BaseModel):
    """3D point with x, y, z coordinates"""
    x: float = Field(..., description="X coordinate in millimeters")
    y: float = Field(..., description="Y coordinate in millimeters")
    z: float = Field(..., description="Z coordinate in millimeters")

class LineLocation(BaseModel):
    """Line defined by two 3D points"""
    p0: Point3D = Field(..., description="Start point")
    p1: Point3D = Field(..., description="End point")

class ElementParameter(BaseModel):
    """Parameter request for an element"""
    element_id: int = Field(..., description="Element ID")
    parameter_name: str = Field(..., description="Parameter name")

class SelectElementsRequest(BaseModel):
    """Request to select elements in Revit"""
    element_ids: List[int] = Field(..., description="List of element IDs to select")

class CategoryRequest(BaseModel):
    """Request for elements in a category"""
    category: str = Field(..., description="Category name (e.g., 'Walls', 'Doors')")
    
class WallCreateRequest(BaseModel):
    """Request to create a wall"""
    start_point: Point3D = Field(..., description="Start point of the wall")
    end_point: Point3D = Field(..., description="End point of the wall")
    height: float = Field(..., description="Height of the wall in millimeters")
    width: float = Field(200.0, description="Width/thickness of the wall in millimeters")
    level_id: Optional[int] = Field(None, description="Level ID (optional)")
    wall_type_id: Optional[int] = Field(None, description="Wall type ID (optional)")

class LineBasedElement(BaseModel):
    """Line-based element creation request"""
    name: str = Field(..., description="Description of the element (e.g., wall, beam)")
    type_id: Optional[int] = Field(None, description="The ID of the family type to create")
    location_line: LineLocation = Field(..., description="The line defining the element's location")
    thickness: float = Field(..., description="Thickness/width of the element in millimeters")
    height: float = Field(..., description="Height of the element in millimeters")
    base_level: Optional[int] = Field(None, description="Base level ID")
    base_offset: float = Field(0.0, description="Offset from the base level in millimeters")

class RevitMCPServer:
    """Main MCP server implementation for Revit integration."""

    def __init__(self, revit_port: int, model: str, api_key: str = None):
        """Initialize the MCP server."""
        global MCP_AVAILABLE
        
        self.revit_port = revit_port
        self.revit_rpc_base_url = f"http://localhost:{revit_port}"
        self.model = model
        self.api_key = api_key
        
        # Log API key status (masked for security)
        if api_key:
            api_key_log = api_key[:4] + "*" * (len(api_key) - 4) if len(api_key) > 4 else "****"
            logger.info(f"API key provided: {api_key_log}")
        else:
            logger.warning("No API key provided")
        
        logger.info(f"Model set to: {model}")
        
        self.uvicorn_server = None
        self.running = True
        
        # Create connection manager for Revit RPC server
        self.revit_connection = RevitConnectionManager(port=revit_port)
        
        # Always create a FastAPI instance first
        self.fastapi_app = FastAPI(
            title="Revit MCP Server",
            description="MCP Server for Revit integration",
            version="0.1.0"
        )
        
        # Add CORS middleware to the FastAPI app
        self.fastapi_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow all origins for local development
            allow_credentials=True,
            allow_methods=["*"],  # Allow all methods
            allow_headers=["*"],  # Allow all headers
        )
        
        # Initialize MCP with our wrapper
        logger.info("Initializing with MCPWrapper")
        self.mcp = MCPWrapper(
            title="Revit MCP Server",
            app=self.fastapi_app
        )
        
        # Update MCP_AVAILABLE based on the wrapper's native MCP status
        MCP_AVAILABLE = self.mcp.has_native_mcp if hasattr(self.mcp, 'has_native_mcp') else False
        
        # Use the FastAPI app for endpoints
        self.app = self.fastapi_app
        
        # Add custom endpoints
        self._setup_endpoints()
        
        # Setup MCP tools in all cases - our wrapper will handle whether there's actual MCP or not
        self._setup_mcp_tools()
    
    def _setup_endpoints(self):
        """Set up custom endpoints for the FastAPI app."""
        @self.app.get("/")
        async def root():
            """Root endpoint, returns HTML interface or status information based on Accept header."""
            # Simple HTML chat interface
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>RevitMCP Chat</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; display: flex; flex-direction: column; height: 100vh; }}
        #chat-container {{ flex: 1; overflow-y: auto; padding: 20px; background-color: #f5f5f5; }}
        .user-message {{ background-color: #e1f5fe; padding: 10px; border-radius: 10px; margin-bottom: 10px; max-width: 80%; align-self: flex-end; margin-left: auto; display: block;}}
        .assistant-message {{ background-color: #ffffff; padding: 10px; border-radius: 10px; margin-bottom: 10px; max-width: 80%; border: 1px solid #e0e0e0; }}
        #input-container {{ display: flex; padding: 10px; background-color: #f0f0f0; border-top: 1px solid #ddd; }}
        #user-input {{ flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
        #send-button {{ padding: 10px 20px; background-color: #2196F3; color: white; border: none; border-radius: 5px; margin-left: 10px; cursor: pointer; }}
        #status {{ padding: 5px 10px; font-size: 12px; color: #666; }}
        .system-message {{ font-style: italic; color: #555; padding: 5px; text-align: center; }}
        .loading {{ display: inline-block; width: 20px; height: 20px; border: 2px solid #f3f3f3; border-radius: 50%; border-top: 2px solid #3498db; animation: spin 1s linear infinite; margin-left: 10px; }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
        pre {{ background-color: #f0f0f0; padding: 8px; border-radius: 4px; overflow-x: auto; }}
        code {{ font-family: monospace; background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px; }}
    </style>
</head>
<body>
    <div id="chat-container"></div>
    <div id="status">Connected to MCP server</div>
    <div id="input-container">
        <textarea id="user-input" placeholder="Ask about the Revit model..." rows="2" style="resize: vertical;"></textarea>
        <button id="send-button">Send</button>
    </div>
    <script>
        const chatContainer = document.getElementById('chat-container');
        const userInput = document.getElementById('user-input');
        const sendButton = document.getElementById('send-button');
        const statusDiv = document.getElementById('status');
        
        // Server settings
        const modelName = "{self.model}";
        
        // Store message history
        let messages = [];
        
        // Check server connection on load
        fetch('/ping', {{
            method: 'GET'
        }})
            .then(response => response.json())
            .then(data => {{
                statusDiv.innerText = "Connected to MCP server";
                statusDiv.style.color = "green";
            }})
            .catch(error => {{
                statusDiv.innerText = "Not connected to MCP server - check server status";
                statusDiv.style.color = "red";
                console.error("Connection error:", error);
            }});
        
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.innerText = text;
            return div.innerHTML;
        }}
        
        function formatMessage(text) {{
            // Simple Markdown-like formatting
            let html = escapeHtml(text);
            
            // Format code blocks
            html = html.replace(/```([\\s\\S]*?)```/g, '<pre>$1</pre>');
            
            // Format inline code
            html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
            
            // Convert line breaks to <br>
            html = html.replace(/\\n/g, '<br>');
            
            return html;
        }}
        
        function addMessage(text, role) {{
            const messageDiv = document.createElement('div');
            
            if (role === 'user') {{
                messageDiv.className = 'user-message';
                messageDiv.innerHTML = formatMessage(text);
            }} else if (role === 'assistant') {{
                messageDiv.className = 'assistant-message';
                messageDiv.innerHTML = formatMessage(text);
            }} else if (role === 'system') {{
                messageDiv.className = 'system-message';
                messageDiv.innerText = text;
            }}
            
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }}
        
        async function sendMessage() {{
            const messageText = userInput.value.trim();
            if (!messageText) return;
            
            // Add to UI
            addMessage(messageText, 'user');
            userInput.value = '';
            
            // Add loading indicator
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'system-message';
            loadingDiv.innerHTML = 'Claude is thinking<div class="loading"></div>';
            chatContainer.appendChild(loadingDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            
            // Add to message history
            messages.push({{
                role: 'user',
                content: messageText
            }});
            
            try {{
                const response = await fetch('/chat', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        messages: messages,
                        model: modelName
                    }})
                }});
                
                // Remove loading indicator
                chatContainer.removeChild(loadingDiv);
                
                const data = await response.json();
                
                if (data.content) {{
                    // Successful response from Claude API
                    const assistantMessage = data.content;
                    addMessage(assistantMessage, 'assistant');
                    
                    // Add to message history
                    messages.push({{
                        role: 'assistant',
                        content: assistantMessage
                    }});
                }} else if (data.error) {{
                    // Error response
                    addMessage('Error: ' + data.error, 'system');
                }} else {{
                    // Unknown response format
                    addMessage('Received unexpected response from server', 'system');
                    console.error("Unexpected response:", data);
                }}
            }} catch (error) {{
                // Remove loading indicator
                chatContainer.removeChild(loadingDiv);
                
                addMessage('Error connecting to server: ' + error.message, 'system');
                statusDiv.innerText = "Connection lost - check server status";
                statusDiv.style.color = "red";
                console.error("Request error:", error);
            }}
        }}
        
        sendButton.addEventListener('click', sendMessage);
        userInput.addEventListener('keydown', (e) => {{
            if (e.key === 'Enter' && !e.shiftKey) {{
                e.preventDefault();
                sendMessage();
            }}
        }});
        
        // Initial greeting
        addMessage('Hello! I\\'m Claude, connected to your Revit model. Ask me anything about your model or how I can help.', 'assistant');
    </script>
</body>
</html>"""
            
            # Check Accept header to determine response format
            accept_header = "text/html"  # Default to HTML
            
            # Return HTML for browser clients
            return HTMLResponse(content=html)
        
        @self.app.get("/health")
        async def health():
            """Health check endpoint."""
            revit_connected = False
            try:
                revit_connected = self.revit_connection.ping()
            except Exception:
                pass
                
            return {
                "status": "healthy",
                "mcp_available": MCP_AVAILABLE,
                "anthropic_available": ANTHROPIC_AVAILABLE,
                "revit_connected": revit_connected
            }
        
        @self.app.get("/ping")
        async def ping():
            """Check if server is running."""
            return {"status": "success", "message": "RevitMCP server is running"}
        
        @self.app.get("/shutdown")
        async def shutdown():
            """Gracefully shutdown the server."""
            logger.info("Received shutdown request")
            # Schedule shutdown after response is sent
            def _shutdown():
                time.sleep(0.5)  # Give server time to send response
                self.stop()
                
            threading.Thread(target=_shutdown).start()
            return {"status": "success", "message": "Server shutting down"}
        
        @self.app.get("/test-revit")
        async def test_revit():
            """Test connection to Revit RPC server."""
            try:
                # Check if the Revit RPC server is available
                is_connected = self.revit_connection.ping()
                
                if is_connected:
                    return {
                        "status": "connected",
                        "message": "Successfully connected to Revit RPC server"
                    }
                else:
                    return {
                        "status": "disconnected",
                        "message": "Revit RPC server is not responding"
                    }
            except Exception as e:
                logger.error(f"Error connecting to Revit RPC server: {e}")
                return {
                    "status": "error",
                    "message": f"Error connecting to Revit: {str(e)}"
                }
        
        @self.app.post("/chat")
        async def chat(request: Request):
            """Handle chat requests from the Revit interface."""
            try:
                # Parse the request body
                body = await request.json()
                messages = body.get("messages", [])
                model = body.get("model", self.model)
                
                logger.info(f"Chat request received: {len(messages)} messages using model '{model}'")
                
                # Generate response using Claude (if available)
                if ANTHROPIC_AVAILABLE and self.api_key:
                    client = anthropic.Anthropic(api_key=self.api_key)
                    
                    try:
                        logger.info(f"Sending request to Claude ({model})...")
                        response = client.messages.create(
                            model=model,
                            messages=messages,
                            max_tokens=4000
                        )
                        
                        logger.info("Claude response received")
                        # Return a simpler response format that the front-end expects
                        return {
                            "role": "assistant",
                            "content": response.content[0].text
                        }
                    except Exception as e:
                        logger.error(f"Error from Claude: {e}")
                        return {
                            "status": "error",
                            "error": str(e)
                        }
                else:
                    # Detailed logging about why the condition failed
                    if not ANTHROPIC_AVAILABLE:
                        logger.error("Anthropic SDK not available - module could not be imported")
                    
                    if not self.api_key:
                        logger.error("API key not provided or empty")
                    elif len(self.api_key) < 10:
                        logger.error(f"API key appears invalid (length: {len(self.api_key)})")
                    
                    error_message = "Anthropic SDK not available or API key not provided"
                    logger.error(error_message)
                    return {
                        "status": "error",
                        "error": error_message
                    }
            except Exception as e:
                logger.error(f"Error processing chat request: {e}")
                logger.error(traceback.format_exc())
                return {
                    "status": "error",
                    "error": str(e)
                }
        
        @self.app.get("/status")
        async def status():
            """API status endpoint, returns status information as JSON."""
            return {
                "status": "running",
                "mcp_available": MCP_AVAILABLE,
                "anthropic_available": ANTHROPIC_AVAILABLE,
                "revit_rpc_url": self.revit_rpc_base_url
            }
    
    def _call_revit_rpc(self, endpoint: str, data: Dict[str, Any]) -> Any:
        """
        Call the Revit RPC server using the connection manager.
        
        Args:
            endpoint: The API endpoint to call
            data: The JSON payload to send
            
        Returns:
            The data returned from the Revit RPC server
            
        Raises:
            ConnectionError: If the connection to Revit fails
            RPCError: If the Revit RPC call fails
        """
        try:
            return self.revit_connection.call_revit_rpc(endpoint, data)
        except (ConnectionError, RPCError) as e:
            # Log but re-raise these specific errors for proper handling
            logger.error(f"Error calling Revit RPC ({endpoint}): {e}")
            raise
        except Exception as e:
            # For unexpected errors, log with stack trace and re-wrap
            logger.error(f"Unexpected error calling Revit RPC ({endpoint}): {e}")
            logger.error(traceback.format_exc())
            raise RPCError(f"Unexpected error communicating with Revit: {str(e)}")
    
    def start(self, mcp_port: int):
        """Start the MCP server."""
        logger.info(f"Starting RevitMCP server on port {mcp_port}")
        logger.info(f"Connecting to Revit RPC server on port {self.revit_port}")
        logger.info(f"MCP functionality: {'Available' if MCP_AVAILABLE else 'Unavailable'}")
        logger.info(f"Claude integration: {'Available' if ANTHROPIC_AVAILABLE else 'Limited'}")
        
        self.running = True
        
        # Start the server
        self.uvicorn_server = uvicorn.Server(
            config=uvicorn.Config(
                app=self.app,
                host="127.0.0.1",
                port=mcp_port,
                log_level="info",
            )
        )
        
        try:
            self.uvicorn_server.run()
        except Exception as e:
            logger.error(f"Error running server: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def stop(self):
        """Stop the MCP server."""
        logger.info("Stopping RevitMCP server")
        self.running = False
        
        # Close the Revit connection
        if hasattr(self, 'revit_connection'):
            self.revit_connection.close()
        
        if self.uvicorn_server:
            self.uvicorn_server.should_exit = True

    def _setup_mcp_tools(self):
        """Set up MCP tools when MCP is available."""
        logger.info("Setting up MCP tools")
        
        # Define tools using our wrapper class
        def get_revit_categories() -> List[str]:
            """
            Get a list of all available categories in the current Revit document.
            
            Returns a list of category names that can be used with other tools like
            get_category_elements.
            """
            logger.info("Tool request: get_revit_categories")
            
            try:
                # Call Revit RPC server
                result = self._call_revit_rpc("get_categories", {})
                
                if not isinstance(result, list):
                    logger.error(f"Invalid response from Revit RPC server: expected list, got {type(result)}")
                    raise MCRError(f"Invalid response from Revit RPC server: expected list, got {type(result)}")
                    
                logger.info(f"Retrieved {len(result)} categories")
                return result
                
            except Exception as e:
                logger.error(f"Error retrieving categories: {e}")
                logger.error(traceback.format_exc())
                raise MCRError(f"Failed to retrieve categories: {str(e)}")
        
        def get_category_elements(category_request: CategoryRequest) -> List[Dict[str, Any]]:
            """
            Get all elements of a specific category in the current Revit document.
            
            Args:
                category_request: The category to get elements for
                
            Returns:
                List of elements with their IDs, names, and categories
            """
            category = category_request.category
            logger.info(f"Tool request: get_category_elements for '{category}'")
            
            try:
                # Call Revit RPC server
                result = self._call_revit_rpc("get_category_elements", {
                    "category": category
                })
                
                if not isinstance(result, list):
                    logger.error(f"Invalid response from Revit RPC server: expected list, got {type(result)}")
                    raise MCRError(f"Invalid response from Revit RPC server: expected list, got {type(result)}")
                    
                logger.info(f"Retrieved {len(result)} elements for category '{category}'")
                return result
                
            except Exception as e:
                logger.error(f"Error retrieving elements for category '{category}': {e}")
                logger.error(traceback.format_exc())
                raise MCRError(f"Failed to retrieve elements: {str(e)}")
        
        def get_element_parameter(param_request: ElementParameter) -> Optional[str]:
            """
            Get a parameter value for a specific element.
            
            Args:
                param_request: Element ID and parameter name to retrieve
                
            Returns:
                The parameter value as a string, or None if the parameter doesn't exist
            """
            element_id = param_request.element_id
            parameter_name = param_request.parameter_name
            
            logger.info(f"Tool request: get_element_parameter for element {element_id}, parameter '{parameter_name}'")
            
            try:
                # Call Revit RPC server
                result = self._call_revit_rpc("get_parameter", {
                    "element_id": element_id,
                    "parameter_name": parameter_name
                })
                
                logger.info(f"Retrieved parameter value: {result}")
                return str(result) if result is not None else None
                
            except Exception as e:
                logger.error(f"Error retrieving parameter: {e}")
                logger.error(traceback.format_exc())
                raise MCRError(f"Failed to retrieve parameter: {str(e)}")
        
        def select_elements(request: SelectElementsRequest) -> int:
            """
            Select elements in Revit by their IDs.
            
            Args:
                request: The element IDs to select
                
            Returns:
                The number of elements successfully selected
            """
            element_ids = request.element_ids
            logger.info(f"Tool request: select_elements for {len(element_ids)} elements")
            
            try:
                # Call Revit RPC server
                result = self._call_revit_rpc("select_elements", {
                    "element_ids": element_ids
                })
                
                # Result should be the number of elements selected
                logger.info(f"Selected {result} elements")
                return int(result)
                
            except Exception as e:
                logger.error(f"Error selecting elements: {e}")
                logger.error(traceback.format_exc())
                raise MCRError(f"Failed to select elements: {str(e)}")

        def create_wall(wall_request: WallCreateRequest) -> Dict[str, Any]:
            """
            Create a wall in Revit.
            
            Args:
                wall_request: Wall parameters including start/end points and height
                
            Returns:
                Information about the created wall including its ID
            """
            logger.info(f"Tool request: create_wall")
            
            try:
                # Convert the Pydantic model to a dict
                data = wall_request.dict()
                
                # Call Revit RPC server
                result = self._call_revit_rpc("create_wall", data)
                
                logger.info(f"Created wall with ID: {result.get('id', 'unknown')}")
                return result
                
            except Exception as e:
                logger.error(f"Error creating wall: {e}")
                logger.error(traceback.format_exc())
                raise MCRError(f"Failed to create wall: {str(e)}")

        def create_line_based_element(element: LineBasedElement) -> Dict[str, Any]:
            """
            Create a line-based element in Revit such as walls, beams, or pipes.
            
            Args:
                element: Element definition including type, location, and dimensions
                
            Returns:
                Information about the created element including its ID
            """
            logger.info(f"Tool request: create_line_based_element for {element.name}")
            
            try:
                # Convert the Pydantic model to a dict
                data = element.dict()
                
                # Call Revit RPC server
                result = self._call_revit_rpc("create_line_based_element", data)
                
                logger.info(f"Created {element.name} with ID: {result.get('id', 'unknown')}")
                return result
                
            except Exception as e:
                logger.error(f"Error creating line-based element: {e}")
                logger.error(traceback.format_exc())
                raise MCRError(f"Failed to create line-based element: {str(e)}")
                
        # Register all tools with our wrapper
        self.mcp.add_tool("get_revit_categories", get_revit_categories, 
                         "Get a list of all available categories in the current Revit document")
        
        self.mcp.add_tool("get_category_elements", get_category_elements,
                         "Get all elements of a specific category in the current Revit document")
        
        self.mcp.add_tool("get_element_parameter", get_element_parameter,
                         "Get a parameter value for a specific element")
        
        self.mcp.add_tool("select_elements", select_elements,
                         "Select elements in Revit by their IDs")
        
        self.mcp.add_tool("create_wall", create_wall,
                         "Create a wall in Revit")
        
        self.mcp.add_tool("create_line_based_element", create_line_based_element,
                         "Create a line-based element in Revit such as walls, beams, or pipes")
        
        # Register MCP resources
        self._register_mcp_components()
    
    def _register_mcp_components(self):
        """Register MCP resources."""
        logger.info("Registering MCP resources")
        
        def get_elements(category: str) -> List[Dict[str, Any]]:
            """Get elements of a specified category from the Revit model."""
            logger.info(f"Resource request: get_elements for category '{category}'")
            
            try:
                # Call Revit RPC server
                result = self._call_revit_rpc("get_elements", {"category": category})
                
                if not isinstance(result, list):
                    logger.error(f"Invalid response from Revit RPC server: expected list, got {type(result)}")
                    raise MCRError(f"Invalid response from Revit RPC server: expected list, got {type(result)}")
                    
                logger.info(f"Retrieved {len(result)} elements for category '{category}'")
                return result
                
            except Exception as e:
                logger.error(f"Error retrieving elements for category '{category}': {e}")
                logger.error(traceback.format_exc())
                raise MCRError(f"Failed to retrieve elements: {str(e)}")
                
        # Register resources with our wrapper
        self.mcp.add_resource("revit://elements/{category}", get_elements,
                             "Get elements of a specified category from the Revit model")

# Define a custom wrapper for MCP functionality
class MCPWrapper:
    """A wrapper class for MCP functionality that adapts to whatever is available"""
    
    def __init__(self, title, app=None):
        self.title = title
        self.app = app
        self.tools = []
        self.resources = []
        
        # Store the original app for later use
        self.fastapi_app = app
        
        # If we have mcp available, try to use its functionality
        if MCP_AVAILABLE:
            try:
                # Try to detect the API style based on the mcp module
                if hasattr(mcp, 'Server'):
                    logger.info("Using mcp.Server based initialization")
                    self.mcp_server = mcp.Server(title)
                    self.has_native_mcp = True
                elif hasattr(mcp.server, 'Server'):
                    logger.info("Using mcp.server.Server based initialization")
                    self.mcp_server = mcp.server.Server(title)
                    self.has_native_mcp = True
                else:
                    logger.warning("MCP available but no Server class found, using lightweight wrapper")
                    self.has_native_mcp = False
            except Exception as e:
                logger.error(f"Error initializing native MCP Server: {e}")
                logger.error(traceback.format_exc())
                self.has_native_mcp = False
        else:
            self.has_native_mcp = False
        
        logger.info(f"MCPWrapper initialized with native MCP: {self.has_native_mcp}")
    
    def add_tool(self, name, fn, description=None):
        """Add a tool to the MCP server or store it locally if MCP is not available"""
        tool_info = {
            "name": name,
            "fn": fn,
            "description": description or fn.__doc__ or ""
        }
        
        if self.has_native_mcp:
            try:
                # Try different ways to register tools based on MCP API
                if hasattr(self.mcp_server, 'add_tool'):
                    # Modern style
                    if hasattr(mcp, 'Tool'):
                        logger.info(f"Registering tool '{name}' using modern MCP API")
                        self.mcp_server.add_tool(mcp.Tool(
                            name=name,
                            fn=fn,
                            description=description or fn.__doc__ or ""
                        ))
                    else:
                        logger.info(f"Registering tool '{name}' using add_tool method")
                        self.mcp_server.add_tool(
                            name=name,
                            fn=fn,
                            description=description or fn.__doc__ or ""
                        )
                elif hasattr(self.mcp_server, 'tool'):
                    # Decorator style
                    logger.info(f"Registering tool '{name}' using decorator style")
                    self.mcp_server.tool(name=name, description=description)(fn)
                else:
                    logger.warning(f"No method found to register tool '{name}' with MCP")
                    self.tools.append(tool_info)
                
                # Successfully registered with MCP
                self.tools.append(tool_info)
                return True
            except Exception as e:
                logger.error(f"Error registering tool '{name}' with MCP: {e}")
                logger.error(traceback.format_exc())
                self.tools.append(tool_info)
                return False
        else:
            # Store locally for our lightweight implementation
            logger.info(f"Storing tool '{name}' in local wrapper (no MCP)")
            self.tools.append(tool_info)
            
            # Add a FastAPI endpoint for this tool if we have access to the app
            if self.fastapi_app:
                @self.fastapi_app.post(f"/tools/{name}")
                async def tool_endpoint(request: Request):
                    try:
                        body = await request.json()
                        args = body.get("args", {})
                        # Call the function with the provided arguments
                        result = fn(**args)
                        return {"status": "success", "result": result}
                    except Exception as e:
                        logger.error(f"Error executing tool '{name}': {e}")
                        logger.error(traceback.format_exc())
                        return {"status": "error", "error": str(e)}
            
            return True
    
    def add_resource(self, name, fn, description=None):
        """Add a resource to the MCP server or store it locally if MCP is not available"""
        resource_info = {
            "name": name,
            "fn": fn,
            "description": description or fn.__doc__ or ""
        }
        
        if self.has_native_mcp:
            try:
                # Try different ways to register resources based on MCP API
                if hasattr(self.mcp_server, 'add_resource'):
                    # Modern style
                    if hasattr(mcp, 'Resource'):
                        logger.info(f"Registering resource '{name}' using modern MCP API")
                        self.mcp_server.add_resource(mcp.Resource(
                            name=name,
                            fn=fn,
                            description=description or fn.__doc__ or ""
                        ))
                    else:
                        logger.info(f"Registering resource '{name}' using add_resource method")
                        self.mcp_server.add_resource(
                            name=name,
                            fn=fn,
                            description=description or fn.__doc__ or ""
                        )
                elif hasattr(self.mcp_server, 'resource'):
                    # Decorator style
                    logger.info(f"Registering resource '{name}' using decorator style")
                    self.mcp_server.resource(name, description=description)(fn)
                else:
                    logger.warning(f"No method found to register resource '{name}' with MCP")
                    self.resources.append(resource_info)
                
                # Successfully registered with MCP
                self.resources.append(resource_info)
                return True
            except Exception as e:
                logger.error(f"Error registering resource '{name}' with MCP: {e}")
                logger.error(traceback.format_exc())
                self.resources.append(resource_info)
                return False
        else:
            # Store locally for our lightweight implementation
            logger.info(f"Storing resource '{name}' in local wrapper (no MCP)")
            self.resources.append(resource_info)
            
            # For resources, we could potentially parse the URL pattern and create FastAPI routes
            # but that's more complex and would require additional parsing logic
            
            return True


def start_server(mcp_port: int, revit_port: int, model: str, api_key: str = None) -> None:
    """Start the MCP server."""
    logger.info(f"Starting server with MCP port: {mcp_port}, Revit port: {revit_port}, Model: {model}")
    server = RevitMCPServer(revit_port, model, api_key)
    server.start(mcp_port)


def test_anthropic_api_key(api_key: str) -> bool:
    """Test if the Anthropic API key is valid by making a minimal API call."""
    if not api_key:
        logger.warning("Cannot test Anthropic API key: No key provided")
        return False
        
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        # Try a simple models.list call which uses minimal tokens
        # and doesn't make a full message completion
        logger.info("Testing Anthropic API key with a models.list call...")
        models = client.models.list()
        
        # If we got this far, the key is valid
        logger.info(f"Anthropic API key test successful. Available models: {[m.id for m in models.data]}")
        return True
    except Exception as e:
        logger.error(f"Anthropic API key test failed: {e}")
        return False


def main():
    """Main entry point for the server."""
    parser = argparse.ArgumentParser(description="RevitMCP Server")
    parser.add_argument("--mcp-port", type=int, default=9876, help="Port for the MCP server")
    parser.add_argument("--revit-port", type=int, default=9877, help="Port for the Revit RPC server")
    parser.add_argument("--model", type=str, default="claude-3-7-sonnet-latest", help="Model for Claude")
    parser.add_argument("--api-key", type=str, help="API key for Claude")
    args = parser.parse_args()
    
    # Check required dependencies
    try:
        logger.info("Checking dependencies...")
        
        # Minimal FastAPI and Uvicorn check
        import fastapi
        import uvicorn
        logger.info(f"FastAPI: {fastapi.__version__}")
        
        # Anthropic check
        try:
            import anthropic
            logger.info(f"Anthropic SDK: {anthropic.__version__}")
            
            # Test API key if provided
            if args.api_key:
                test_anthropic_api_key(args.api_key)
            else:
                logger.warning("No API key provided. Claude integration will be limited.")
        except (ImportError, AttributeError):
            logger.warning("Anthropic SDK not available")
            
        # MCP check
        try:
            import mcp
            logger.info(f"MCP SDK available")
            # Just log that it's available, we'll handle the details later
        except ImportError:
            logger.warning("MCP SDK not available")
    except ImportError as e:
        logger.error(f"Missing required dependency: {e}")
        logger.error("Please install required packages: pip install -r requirements.txt")
        return 1
    
    try:
        # Create server - our wrapper will handle MCP availability
        server = RevitMCPServer(args.revit_port, args.model, args.api_key)
        
        # Handle graceful shutdown on CTRL+C
        def signal_handler(sig, frame):
            logger.info("Received signal, shutting down...")
            server.stop()
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start server
        server.start(args.mcp_port)
        
        return 0
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main()) 