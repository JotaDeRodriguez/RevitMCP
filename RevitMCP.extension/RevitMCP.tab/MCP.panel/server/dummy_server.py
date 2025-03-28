"""
MCP Server - Dummy Implementation
Provides a simple HTTP server for MCP testing
"""
import os
import sys
import json
import time
import threading
import socket
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import datetime
import platform

# Add lib directory to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
LIB_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "lib")
if LIB_DIR not in sys.path:
    sys.path.append(LIB_DIR)

# Try to import server registry
try:
    from lib.server_registry import update_registry, log_message
except ImportError:
    # Define fallback logging function if import fails
    def log_message(message, level="INFO"):
        """Log a message to the server log file"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(os.path.join(SCRIPT_DIR, "server_log.txt"), "a") as f:
            f.write("[{}] [{}] {}\n".format(timestamp, level, message))
    
    # Define fallback update_registry function
    def update_registry(status, pid=None, mcp_port=9876, revit_port=9877):
        """Log registry update since import failed"""
        log_message("Would update registry: status={}, pid={}, mcp_port={}, revit_port={}".format(status, pid, mcp_port, revit_port), "INFO")

# Default ports
DEFAULT_MCP_PORT = 9876
DEFAULT_REVIT_PORT = 9877

# Server state
server_state = {
    "running": True,
    "mcp_port": DEFAULT_MCP_PORT,
    "revit_port": DEFAULT_REVIT_PORT,
    "start_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

# Resources
available_resources = {
    "models": [
        {"id": "gpt-4", "name": "GPT-4", "description": "Advanced LLM model"},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "description": "Fast LLM model"}
    ],
    "revit_elements": [
        {"type": "Wall", "count": 42},
        {"type": "Door", "count": 12},
        {"type": "Window", "count": 24},
        {"type": "Floor", "count": 8}
    ]
}

class MCPRequestHandler(BaseHTTPRequestHandler):
    """Request handler for the MCP server"""
    
    def log_message(self, format, *args):
        """Override log_message to use our logging system"""
        log_message("{} - {}".format(self.address_string(), format % args), "INFO")
    
    def log_error(self, format, *args):
        """Override log_error to use our logging system"""
        log_message("ERROR: {} - {}".format(self.address_string(), format % args), "ERROR")
    
    def send_json_response(self, data, status=200):
        """Helper method to send a JSON response"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = json.dumps(data, indent=2)
        self.wfile.write(response.encode('utf-8'))
    
    def send_text_response(self, text, status=200):
        """Helper method to send a text response"""
        self.send_response(status)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        self.wfile.write(text.encode('utf-8'))
    
    def handle_error(self, error_message, status=500):
        """Helper method to handle errors"""
        log_message("Error: {}".format(error_message), "ERROR")
        self.send_json_response({"error": error_message}, status)
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            # Parse URL
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            # Resources endpoint
            if path == '/api/v1/resources':
                self.send_json_response(available_resources)
            
            # Server status endpoint
            elif path == '/status':
                status = {
                    "status": "running" if server_state["running"] else "stopped",
                    "uptime": str(datetime.datetime.now() - datetime.datetime.strptime(server_state["start_time"], "%Y-%m-%d %H:%M:%S")),
                    "mcp_port": server_state["mcp_port"],
                    "revit_port": server_state["revit_port"]
                }
                self.send_json_response(status)
            
            # Shutdown endpoint
            elif path == '/shutdown':
                log_message("Received shutdown request", "INFO")
                self.send_text_response("Server shutting down...", 200)
                
                # Start a thread to shut down the server after response is sent
                threading.Thread(target=self.server.shutdown).start()
                
                # Update registry
                update_registry("stopped")
            
            # Unknown endpoint
            else:
                self.handle_error("Unknown endpoint: {}".format(path), 404)
        
        except Exception as e:
            self.handle_error("Error processing GET request: {}".format(str(e)))
            log_message(traceback.format_exc(), "ERROR")
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            # Parse URL
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            # Parse JSON body
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self.handle_error("Invalid JSON body", 400)
                return
            
            # Generate endpoint
            if path == '/api/v1/generate':
                log_message("Generate request: {}...".format(json.dumps(data)[:100]), "INFO")
                
                # Extract messages from request
                messages = data.get('messages', [])
                user_message = None
                
                # Find the user message
                for message in messages:
                    if message.get('role') == 'user':
                        user_message = message.get('content', '')
                        break
                
                if not user_message:
                    self.handle_error("No user message found in request", 400)
                    return
                
                # Generate a dummy response based on the user message
                response_content = self.generate_dummy_response(user_message)
                
                # Create response
                response = {
                    "id": "dummy-response-" + datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": "dummy-mcp-model",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": response_content
                            },
                            "finish_reason": "stop"
                        }
                    ]
                }
                
                self.send_json_response(response)
            
            # Unknown endpoint
            else:
                self.handle_error("Unknown endpoint: {}".format(path), 404)
        
        except Exception as e:
            self.handle_error("Error processing POST request: {}".format(str(e)))
            log_message(traceback.format_exc(), "ERROR")
    
    def generate_dummy_response(self, user_message):
        """Generate a dummy response based on the user message"""
        # Convert to lowercase for easier matching
        message_lower = user_message.lower()
        
        # Check for element types
        if "wall" in message_lower:
            return """I found 42 walls in your Revit model. Here's a summary:
- 28 Basic Walls (Wall-Ext-152 Brick and CMU on MTL Stud)
- 14 Interior Walls (Wall-Int-78 Stud)

The total length of all walls is approximately 325.6 meters. The average height is 3.2 meters."""
        
        elif "door" in message_lower:
            return """I found 12 doors in your Revit model. Here's a summary:
- 8 Single-Flush doors (36" x 84")
- 4 Double-Glass doors (72" x 84")

All doors are appropriately hosted in walls."""
        
        elif "window" in message_lower:
            return """I found 24 windows in your Revit model. Here's a summary:
- 16 Fixed windows (36" x 48")
- 8 Double-Hung windows (36" x 72")

All windows are properly hosted in exterior walls."""
        
        elif "floor" in message_lower:
            return """I found 8 floors in your Revit model. Here's a summary:
- 6 standard floors (Floor: Generic 12")
- 2 ground floors (Floor: Slab on Grade 6")

The total floor area is approximately 2,450 square meters."""
        
        elif "element" in message_lower or "model" in message_lower:
            return """Your Revit model contains the following elements:
- 42 Walls
- 12 Doors
- 24 Windows
- 8 Floors
- 16 Structural Columns
- 12 Lighting Fixtures
- 8 Plumbing Fixtures

Would you like more detailed information about any specific element type?"""
        
        # Generic response
        else:
            return f"""I'm a dummy MCP server responding to your query about "{user_message}".

Since this is a test server, I don't have actual access to your Revit model data.
In a real implementation, I would analyze your model and provide meaningful information.

You can ask me about walls, doors, windows, floors, or other model elements to see example responses."""

def get_free_port(start_port):
    """Find a free port starting from the given port"""
    port = start_port
    max_port = start_port + 100  # Try up to 100 ports after the start port
    
    while port < max_port:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            if result != 0:  # Port is available
                return port
            
            port += 1
        except:
            port += 1
    
    # If we couldn't find a free port, return the original
    return start_port

def run_server(mcp_port, revit_port):
    """Run the MCP server"""
    # Update registry with starting status
    update_registry("starting", os.getpid(), mcp_port, revit_port)
    
    # Log startup information
    log_message("Starting MCP server on port {}".format(mcp_port), "INFO")
    log_message("Python version: {}".format(sys.version), "INFO")
    log_message("Platform: {}".format(platform.platform()), "INFO")
    
    # Create server
    server = HTTPServer(('localhost', mcp_port), MCPRequestHandler)
    
    # Update registry with running status
    update_registry("running", os.getpid(), mcp_port, revit_port)
    
    # Update server state
    server_state["mcp_port"] = mcp_port
    server_state["revit_port"] = revit_port
    
    # Log server ready
    log_message("MCP server running at http://localhost:{}".format(mcp_port))
    
    # Start server
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        log_message("Server error: {}".format(str(e)), "ERROR")
        log_message(traceback.format_exc(), "ERROR")
    finally:
        # Update registry with stopped status
        update_registry("stopped")
        log_message("Server stopped")

def main():
    """Main entry point for the server"""
    # Default ports
    mcp_port = DEFAULT_MCP_PORT
    revit_port = DEFAULT_REVIT_PORT
    
    try:
        # Get command line arguments if provided
        if len(sys.argv) > 1:
            try:
                mcp_port = int(sys.argv[1])
            except ValueError:
                log_message("Invalid MCP port: {}, using default: {}".format(sys.argv[1], DEFAULT_MCP_PORT), "WARNING")
        
        if len(sys.argv) > 2:
            try:
                revit_port = int(sys.argv[2])
            except ValueError:
                log_message("Invalid Revit port: {}, using default: {}".format(sys.argv[2], DEFAULT_REVIT_PORT), "WARNING")
        
        # Verify ports are free
        mcp_port = get_free_port(mcp_port)
        revit_port = get_free_port(revit_port)
        
        # Run server
        run_server(mcp_port, revit_port)
    
    except Exception as e:
        log_message("Fatal error: {}".format(str(e)), "ERROR")
        log_message(traceback.format_exc(), "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main() 