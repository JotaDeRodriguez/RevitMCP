"""
Server Registry Manager
Handles tracking of MCP server status, startup and shutdown
"""
import os
import json
import time
import socket
import sys
import platform
import datetime

# Compatibility for IronPython and CPython
try:
    import clr
    RUNNING_IRONPYTHON = True
except ImportError:
    RUNNING_IRONPYTHON = False

# Set up paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REGISTRY_FILE = os.path.join(SCRIPT_DIR, "server_registry.json")
SERVER_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "server")
LAUNCHER_PATH = os.path.join(SERVER_DIR, "server_launcher.bat")
LOG_FILE = os.path.join(SERVER_DIR, "server_log.txt")

# Default server settings
DEFAULT_MCP_PORT = 9876
DEFAULT_REVIT_PORT = 9877

def log_message(message, level="INFO"):
    """Log a message to the server log file"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write("[{}] [{}] [Registry] {}\n".format(timestamp, level, message))

def get_registry():
    """Get the current server registry information"""
    if not os.path.exists(REGISTRY_FILE):
        return {"status": "stopped", "pid": None, "mcp_port": DEFAULT_MCP_PORT, "revit_port": DEFAULT_REVIT_PORT}
    
    try:
        with open(REGISTRY_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        log_message("Error reading registry: {}".format(str(e)), "ERROR")
        return {"status": "unknown", "pid": None, "mcp_port": DEFAULT_MCP_PORT, "revit_port": DEFAULT_REVIT_PORT}

def update_registry(status, pid=None, mcp_port=DEFAULT_MCP_PORT, revit_port=DEFAULT_REVIT_PORT):
    """Update the server registry with new status"""
    registry = {
        "status": status,
        "pid": pid,
        "mcp_port": mcp_port,
        "revit_port": revit_port,
        "last_update": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        with open(REGISTRY_FILE, "w") as f:
            json.dump(registry, f, indent=2)
        return True
    except Exception as e:
        log_message("Error updating registry: {}".format(str(e)), "ERROR")
        return False

def is_port_in_use(port):
    """Check if a port is in use"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    except:
        return False

def is_server_running():
    """Check if the MCP server is running"""
    registry = get_registry()
    
    # If registry says running, verify it's actually running
    if registry["status"] in ["running", "starting"]:
        mcp_port = registry.get("mcp_port", DEFAULT_MCP_PORT)
        
        # Check if port is in use
        if is_port_in_use(mcp_port):
            if registry["status"] == "starting":
                update_registry("running", registry.get("pid"), mcp_port, registry.get("revit_port", DEFAULT_REVIT_PORT))
            return True
        else:
            # Port not in use but registry says running - update registry
            update_registry("stopped")
            return False
    
    return False

def start_server(mcp_port=DEFAULT_MCP_PORT, revit_port=DEFAULT_REVIT_PORT):
    """Start the MCP server using the launcher script"""
    if is_server_running():
        log_message("Server already running - not starting a new instance")
        return True
    
    log_message("Starting MCP server on ports {} (MCP) and {} (Revit)".format(mcp_port, revit_port))
    
    # Ensure launcher exists
    if not os.path.exists(LAUNCHER_PATH):
        log_message("Launcher script not found at: {}".format(LAUNCHER_PATH), "ERROR")
        return False
    
    try:
        # Launch server using appropriate method for the OS
        if platform.system() == "Windows":
            if RUNNING_IRONPYTHON:
                # Use shell execute to avoid IronPython subprocess issues
                import System.Diagnostics
                launcher_params = "{} {}".format(mcp_port, revit_port)
                
                # Start the process and get its PID
                process = System.Diagnostics.Process.Start(LAUNCHER_PATH, launcher_params)
                pid = process.Id
                
                # Update registry with starting status
                update_registry("starting", pid, mcp_port, revit_port)
                
                # Wait for server to become available
                max_wait = 30  # seconds
                for i in range(max_wait):
                    time.sleep(1)
                    if is_port_in_use(mcp_port):
                        update_registry("running", pid, mcp_port, revit_port)
                        return True
                
                # Timeout waiting for server
                log_message("Timeout waiting for server to start on port {}".format(mcp_port), "WARNING")
                return False
            else:
                # Standard Python on Windows
                import subprocess
                cmd = 'start /b "" "{}" {} {}'.format(LAUNCHER_PATH, mcp_port, revit_port)
                os.system(cmd)
        else:
            # Unix-like systems
            import subprocess
            cmd = "bash {} {} {} &".format(LAUNCHER_PATH, mcp_port, revit_port)
            subprocess.Popen(cmd, shell=True)
        
        # Wait for server to become available
        max_wait = 30  # seconds
        for i in range(max_wait):
            time.sleep(1)
            if is_port_in_use(mcp_port):
                return True
        
        # Timeout waiting for server
        log_message("Timeout waiting for server to start on port {}".format(mcp_port), "WARNING")
        return False
        
    except Exception as e:
        log_message("Error starting server: {}".format(str(e)), "ERROR")
        return False

def stop_server():
    """Stop the MCP server by sending shutdown request"""
    if not is_server_running():
        return True
    
    registry = get_registry()
    mcp_port = registry.get("mcp_port", DEFAULT_MCP_PORT)
    
    try:
        # Try to send shutdown request to server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('127.0.0.1', mcp_port))
        
        shutdown_request = "GET /shutdown HTTP/1.1\r\nHost: localhost\r\n\r\n"
        sock.sendall(shutdown_request.encode())
        sock.close()
        
        # Wait for server to actually shut down
        max_wait = 10  # seconds
        for i in range(max_wait):
            time.sleep(1)
            if not is_port_in_use(mcp_port):
                update_registry("stopped")
                return True
        
        # Force update registry anyway
        update_registry("stopped")
        log_message("Server did not shut down gracefully", "WARNING")
        return False
    except Exception as e:
        log_message("Error stopping server: {}".format(str(e)), "ERROR")
        update_registry("unknown")
        return False

def get_server_url():
    """Get the URL for the MCP server"""
    registry = get_registry()
    mcp_port = registry.get("mcp_port", DEFAULT_MCP_PORT)
    return "http://localhost:{}".format(mcp_port)

def get_server_status():
    """Get detailed server status information"""
    registry = get_registry()
    status = registry.get("status", "unknown")
    
    # Verify if server is actually running
    mcp_port = registry.get("mcp_port", DEFAULT_MCP_PORT)
    port_active = is_port_in_use(mcp_port)
    
    if status in ["running", "starting"] and not port_active:
        update_registry("stopped")
        status = "stopped"
    elif status != "running" and port_active:
        update_registry("running", registry.get("pid"), mcp_port, registry.get("revit_port", DEFAULT_REVIT_PORT))
        status = "running"
    
    return {
        "status": status,
        "url": get_server_url() if status == "running" else None,
        "mcp_port": mcp_port,
        "revit_port": registry.get("revit_port", DEFAULT_REVIT_PORT),
        "last_update": registry.get("last_update", "unknown")
    }

# Initialize registry if it doesn't exist
if not os.path.exists(REGISTRY_FILE):
    update_registry("stopped")

# Create log file if it doesn't exist
if not os.path.exists(os.path.dirname(LOG_FILE)):
    os.makedirs(os.path.dirname(LOG_FILE))
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w") as f:
        f.write("[{}] [INFO] [Registry] Log file created\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))) 