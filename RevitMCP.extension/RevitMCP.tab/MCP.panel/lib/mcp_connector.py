"""
MCP Connector Module
Handles connection to MCP server and Revit API integration
"""
import os
import sys
import time
import json
import socket
import platform
import traceback

# Add lib directory to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

# Import server registry module
from server_registry import (
    start_server, 
    stop_server, 
    is_server_running, 
    get_server_status, 
    get_server_url,
    log_message
)

# Default settings
DEFAULT_MCP_PORT = 9876
DEFAULT_REVIT_PORT = 9877
SETTINGS_FILE = os.path.join(SCRIPT_DIR, "mcp_settings.json")

def load_settings():
    """Load MCP connector settings from file"""
    if not os.path.exists(SETTINGS_FILE):
        return {
            "mcp_port": DEFAULT_MCP_PORT,
            "revit_port": DEFAULT_REVIT_PORT,
            "api_key": "",
            "model": "claude-3-7-sonnet-20250219",
            "auto_start_server": True
        }
    
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        log_message("Error loading settings: {}".format(str(e)), "ERROR")
        return {
            "mcp_port": DEFAULT_MCP_PORT,
            "revit_port": DEFAULT_REVIT_PORT,
            "api_key": "",
            "model": "claude-3-7-sonnet-20250219",
            "auto_start_server": True
        }

def save_settings(settings):
    """Save MCP connector settings to file"""
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        log_message("Error saving settings: {}".format(str(e)), "ERROR")
        return False

def ensure_server_running():
    """Ensure the MCP server is running, starting it if needed"""
    if is_server_running():
        return True
    
    settings = load_settings()
    if settings.get("auto_start_server", True):
        return start_server(
            settings.get("mcp_port", DEFAULT_MCP_PORT), 
            settings.get("revit_port", DEFAULT_REVIT_PORT)
        )
    
    return False

def send_request(endpoint, method="GET", data=None, timeout=10):
    """Send a request to the MCP server"""
    if not ensure_server_running():
        raise ConnectionError("Failed to start MCP server")
    
    server_url = get_server_url()
    url = "{}{}".format(server_url, endpoint.lstrip('/'))
    
    try:
        # Create a socket connection to the server
        parsed_url = url.split("://")[1]
        host = parsed_url.split("/")[0].split(":")[0]
        port = int(parsed_url.split("/")[0].split(":")[1]) if ":" in parsed_url.split("/")[0] else 80
        path = "/" + "/".join(parsed_url.split("/")[1:])
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        
        # Create HTTP request
        request_lines = ["{} {} HTTP/1.1".format(method, path), "Host: {}:{}".format(host, port)]
        
        if data:
            json_data = json.dumps(data)
            request_lines.extend([
                "Content-Type: application/json",
                "Content-Length: {}".format(len(json_data)),
                "",
                json_data
            ])
        else:
            request_lines.extend(["", ""])
        
        request = "\r\n".join(request_lines)
        sock.sendall(request.encode())
        
        # Get response
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
        
        sock.close()
        
        # Parse response
        response_text = response.decode("utf-8")
        headers, body = response_text.split("\r\n\r\n", 1)
        
        # Extract status code
        status_line = headers.split("\r\n")[0]
        status_code = int(status_line.split(" ")[1])
        
        # Return parsed response
        if status_code >= 400:
            log_message("Error response from server: {} - {}".format(status_code, body), "ERROR")
            raise ConnectionError("Server error: {}".format(status_code))
        
        try:
            return json.loads(body)
        except:
            return body
        
    except Exception as e:
        log_message("Error sending request to {}: {}".format(url, str(e)), "ERROR")
        log_message(traceback.format_exc(), "DEBUG")
        raise ConnectionError("Failed to communicate with MCP server: {}".format(str(e)))

def generate_response(prompt, system_message=None):
    """Generate a response from the MCP server"""
    # Prepare request data
    data = {
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    if system_message:
        data["messages"].insert(0, {"role": "system", "content": system_message})
    
    # Send request to server
    try:
        response = send_request("api/v1/generate", method="POST", data=data)
        return response.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        log_message("Error generating response: {}".format(str(e)), "ERROR")
        raise

def get_resources():
    """Get available resources from the MCP server"""
    try:
        return send_request("api/v1/resources")
    except Exception as e:
        log_message("Error getting resources: {}".format(str(e)), "ERROR")
        raise 