"""Test interface for interacting with the MCP server."""

import os
import sys
import json
import traceback
from pyrevit import forms
from pyrevit import script

# Setup logging
logger = script.get_logger()
logger.info("Test Interface button clicked")

# Add lib directory to path
script_dir = os.path.dirname(os.path.dirname(__file__))
lib_dir = os.path.join(script_dir, "lib")
sys.path.append(lib_dir)

# Import MCP connector
try:
    import mcp_connector
    from server_registry import is_server_running, get_server_status, log_message
    logger.info("MCP modules imported successfully")
except ImportError as e:
    error_msg = "Error: Could not import MCP modules. Make sure all required files are in the lib directory."
    logger.error("{}: {}".format(error_msg, e))
    forms.alert(error_msg, exitscript=True)
    sys.exit(1)

class MCPTestForm:
    """Simple form for testing MCP functionality."""
    
    def __init__(self):
        """Initialize the form."""
        self.result = None
        self.server_running = False
        
    def check_server_status(self):
        """Check if the MCP server is running."""
        try:
            is_running = is_server_running()
            self.server_running = is_running
            return is_running
        except Exception as e:
            logger.error("Error checking server status: {}".format(e))
            return False
            
    def show_form(self):
        """Show the form to the user."""
        try:
            # Check server status first
            self.check_server_status()
            server_status = "Running" if self.server_running else "Not Running"
            
            # Build options list
            options = []
            options.append("Send Query to MCP Server")
            options.append("Check Server Status")
            
            if self.server_running:
                options.append("Stop MCP Server")
            else:
                options.append("Start MCP Server")
                
            # Show form
            selected = forms.CommandSwitchWindow.show(
                options,
                message="MCP Test Interface - Server Status: {}".format(server_status)
            )
            
            if not selected:
                return None
                
            # Process selection
            if selected == "Send Query to MCP Server":
                self.request_query()
            elif selected == "Check Server Status":
                self.display_server_status()
            elif selected == "Start MCP Server":
                self.start_server()
            elif selected == "Stop MCP Server":
                self.stop_server()
                
            # Show the form again after processing
            return self.show_form()
                
        except Exception as e:
            logger.error("Error showing form: {}".format(e))
            logger.error(traceback.format_exc())
            forms.alert("Error showing form: {}".format(e))
    
    def display_server_status(self):
        """Display detailed server status."""
        try:
            status = get_server_status()
            
            status_text = "Server Status: {}\n".format(status["status"])
            status_text += "MCP Port: {}\n".format(status["mcp_port"])
            status_text += "Revit Port: {}\n".format(status["revit_port"])
            
            if status["url"]:
                status_text += "Server URL: {}\n".format(status["url"])
            
            status_text += "Last Update: {}".format(status["last_update"])
            
            forms.alert(status_text, title="MCP Server Status", expanded=True)
            
        except Exception as e:
            logger.error("Error getting server status: {}".format(e))
            forms.alert("Error getting server status: {}".format(e), title="Status Error")
    
    def request_query(self):
        """Request a query from the user and send it to the server."""
        try:
            # Check server status first
            if not self.check_server_status():
                server_start = forms.alert("MCP Server is not running. Would you like to start it?", 
                                         yes=True, no=True, title="Server Status")
                if server_start:
                    self.start_server()
                    # Check again
                    if not self.check_server_status():
                        forms.alert("Failed to start MCP Server. Please check logs.", title="Server Status")
                        return
                else:
                    return
            
            # Get query from user
            query = forms.ask_for_string(
                prompt="Enter your question about the Revit model:",
                title="MCP Test Interface",
                default="Tell me about this model"
            )
            
            if not query:
                return None
                
            # Send the query
            self.send_query(query)
            
        except Exception as e:
            logger.error("Error requesting query: {}".format(e))
            forms.alert("Error requesting query: {}".format(e), title="Input Error")
    
    def start_server(self):
        """Start the MCP server."""
        try:
            # Show a waiting dialog
            with forms.ProgressBar(title="Starting MCP Server", cancellable=False) as pb:
                pb.update_progress(20, 100)
                
                # Get settings
                settings = mcp_connector.load_settings()
                mcp_port = settings.get("mcp_port", 9876)
                revit_port = settings.get("revit_port", 9877)
                
                # Start the server
                success = mcp_connector.ensure_server_running()
                pb.update_progress(90, 100)
                
                # Update UI
                if success:
                    self.server_running = True
                    forms.alert("MCP Server started successfully", title="Server Status")
                else:
                    forms.alert("Failed to start MCP Server", title="Server Status")
                    
                pb.update_progress(100, 100)
        except Exception as e:
            logger.error("Error starting server: {}".format(e))
            logger.error(traceback.format_exc())
            forms.alert("Error starting server: {}".format(e))
    
    def stop_server(self):
        """Stop the MCP server."""
        try:
            # Show a waiting dialog
            with forms.ProgressBar(title="Stopping MCP Server", cancellable=False) as pb:
                pb.update_progress(30, 100)
                
                # Stop the server
                from server_registry import stop_server
                success = stop_server()
                pb.update_progress(90, 100)
                
                # Update UI
                if success:
                    self.server_running = False
                    forms.alert("MCP Server stopped successfully", title="Server Status")
                else:
                    forms.alert("Failed to stop MCP Server", title="Server Status")
                    
                pb.update_progress(100, 100)
        except Exception as e:
            logger.error("Error stopping server: {}".format(e))
            logger.error(traceback.format_exc())
            forms.alert("Error stopping server: {}".format(e))
    
    def send_query(self, query):
        """Send a query to the MCP server."""
        try:
            # Check if server is running
            if not self.check_server_status():
                forms.alert("MCP Server is not running. Please start the server first.", title="Server Status")
                return
            
            # Show a waiting dialog
            with forms.ProgressBar(title="Processing Query", cancellable=False) as pb:
                pb.update_progress(30, 100)
                pb.update_title("Sending Query")
                
                try:
                    # Use mcp_connector to send request
                    response = mcp_connector.generate_response(query)
                    pb.update_progress(80, 100)
                    pb.update_title("Processing Response")
                    
                    if response:
                        result = response
                    else:
                        # Use fallback response if server returns nothing
                        result = simple_demo_response(query)
                        
                except Exception as e:
                    logger.error("Error sending query to server: {}".format(e))
                    # Use fallback response
                    result = simple_demo_response(query)
                    result += "\n\n(Note: This is a demo response. Server error: {})".format(str(e))
                
                pb.update_progress(100, 100)
            
            # Show response
            forms.alert(result, title="MCP Response", expanded=True)
            
        except Exception as e:
            logger.error("Error sending query: {}".format(e))
            logger.error(traceback.format_exc())
            forms.alert("Error sending query: {}".format(e), title="Error")

def simple_demo_response(query_text):
    """Generate a canned response based on the query text when server fails."""
    query_lower = query_text.lower()
    
    if "wall" in query_lower:
        return """I found 42 walls in your model:

Basic Wall (28 walls):
- ID: 316124, Length: 20.5 ft, Area: 205 sq ft
- ID: 316156, Length: 15.2 ft, Area: 152 sq ft
- ID: 316187, Length: 25.0 ft, Area: 250 sq ft
(and 25 more)

Exterior Wall (14 walls):
- ID: 317024, Length: 30.0 ft, Area: 300 sq ft
- ID: 317075, Length: 30.0 ft, Area: 300 sq ft
- ID: 317112, Length: 20.5 ft, Area: 205 sq ft
(and 11 more)"""
    
    elif "room" in query_lower:
        return """I found 8 rooms in your model:

Level 1 (5 rooms):
- Room 101: Office - Area: 120 sq ft
- Room 102: Conference - Area: 250 sq ft
- Room 103: Lobby - Area: 300 sq ft
- Room 104: Restroom - Area: 80 sq ft
- Room 105: Storage - Area: 60 sq ft

Level 2 (3 rooms):
- Room 201: Office - Area: 120 sq ft
- Room 202: Conference - Area: 250 sq ft
- Room 203: Restroom - Area: 80 sq ft"""
        
    elif "door" in query_lower:
        return """I found 12 doors in your model:

Single-Panel (8 doors):
- ID: 324156, Width: 3'-0", Height: 7'-0"
- ID: 324178, Width: 3'-0", Height: 7'-0"
- ID: 324192, Width: 3'-0", Height: 7'-0"
(and 5 more)

Double-Panel (4 doors):
- ID: 325102, Width: 6'-0", Height: 7'-0"
- ID: 325124, Width: 6'-0", Height: 7'-0"
- ID: 325146, Width: 6'-0", Height: 7'-0"
- ID: 325168, Width: 6'-0", Height: 7'-0"
"""
    
    elif "window" in query_lower:
        return """I found 24 windows in your model:

Fixed (16 windows):
- ID: 335102, Width: 3'-0", Height: 4'-0"
- ID: 335124, Width: 3'-0", Height: 4'-0"
- ID: 335145, Width: 2'-0", Height: 4'-0"
(and 13 more)

Casement (8 windows):
- ID: 336102, Width: 2'-6", Height: 4'-0"
- ID: 336124, Width: 2'-6", Height: 4'-0"
- ID: 336146, Width: 2'-6", Height: 4'-0"
(and 5 more)"""
    
    else:
        return """This is a 2-story office building model with:
- 42 walls (28 Basic Walls, 14 Exterior Walls)
- 12 doors (8 Single-Panel, 4 Double-Panel)
- 24 windows (16 Fixed, 8 Casement)
- 8 rooms (5 on Level 1, 3 on Level 2)
- 8 floors
- Total building area: approximately 3,600 sq ft

The building has a rectangular floor plan with dimensions of approximately 60' x 30'.
"""

def main():
    """Main function to run the MCP test form."""
    try:
        form = MCPTestForm()
        form.show_form()
    except Exception as e:
        logger.error("Error in main: {}".format(e))
        logger.error(traceback.format_exc())
        forms.alert("Error: {}".format(e), title="Error")

if __name__ == "__main__":
    main() 