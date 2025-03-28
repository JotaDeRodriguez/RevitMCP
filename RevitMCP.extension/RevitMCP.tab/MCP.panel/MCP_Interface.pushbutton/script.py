"""MCP interface for interacting with the MCP server."""

import os
import sys
import json
import traceback
from pyrevit import forms
from pyrevit import script
import threading
import time
import clr

# Import WPF
clr.AddReference("PresentationFramework")
clr.AddReference("PresentationCore")
import System.Windows
from System.Windows import Application, Window
from System.Windows.Controls import TextBox, Button, StackPanel
import wpf

# Setup logging
logger = script.get_logger()
logger.info("MCP Interface button clicked")

# Add lib directory to path
script_dir = os.path.dirname(os.path.dirname(__file__))
lib_dir = os.path.join(script_dir, "lib")
sys.path.append(lib_dir)

# Import MCP connector
try:
    import mcp_connector
except ImportError:
    forms.alert("Error: Could not import mcp_connector module. Make sure all required files are in the lib directory.", exitscript=True)
    sys.exit(1)

class MCPInterfaceForm(forms.WPFWindow):
    """WPF form for MCP Interface with console-style display."""
    
    def __init__(self):
        """Initialize the MCP Interface form."""
        try:
            # Set up form from XAML or create it programmatically
            xaml_file = os.path.join(os.path.dirname(__file__), 'MCPInterfaceForm.xaml')
            if os.path.exists(xaml_file):
                wpf.LoadComponent(self, xaml_file)
            else:
                # No XAML file, set up form programmatically
                self.setup_form()
            
            # Initialize form properties
            self.Title = "MCP Interface"
            
            # Get settings
            self.settings = mcp_connector.load_settings()
            self.mcp_port = self.settings["mcp_server_port"]
            
            # Set up event handlers if not already set in XAML
            self.setup_events()
            
            # Initialize message display
            self.messages = []
            
            # Check if server is running, start if not
            self.check_server()
            
        except Exception as e:
            logger.error("Error initializing MCPInterfaceForm: {}".format(e))
            logger.error(traceback.format_exc())
            forms.alert("Error initializing interface: {}".format(e), exitscript=True)
    
    def setup_form(self):
        """Set up the form programmatically if no XAML file exists."""
        # Create main grid
        self.Width = 600
        self.Height = 500
        self.MinWidth = 400
        self.MinHeight = 300
        
        # Initialize UI elements programmatically
        self.chat_history = TextBox()
        self.chat_history.AcceptsReturn = True
        self.chat_history.IsReadOnly = True
        self.chat_history.VerticalScrollBarVisibility = System.Windows.Controls.ScrollBarVisibility.Auto
        self.chat_history.HorizontalScrollBarVisibility = System.Windows.Controls.ScrollBarVisibility.Auto
        self.chat_history.TextWrapping = System.Windows.TextWrapping.Wrap
        self.chat_history.Margin = System.Windows.Thickness(10, 10, 10, 10)
        self.chat_history.FontFamily = System.Windows.Media.FontFamily("Consolas")
        
        self.user_input = TextBox()
        self.user_input.AcceptsReturn = True
        self.user_input.Height = 60
        self.user_input.Margin = System.Windows.Thickness(10, 0, 10, 5)
        
        self.send_button = Button()
        self.send_button.Content = "Send"
        self.send_button.Height = 30
        self.send_button.Margin = System.Windows.Thickness(10, 0, 10, 10)
        
        # Create stack panel
        stack_panel = StackPanel()
        stack_panel.Children.Add(self.chat_history)
        stack_panel.Children.Add(self.user_input)
        stack_panel.Children.Add(self.send_button)
        
        # Set as content
        self.Content = stack_panel
    
    def setup_events(self):
        """Set up event handlers for UI elements."""
        try:
            # Find elements if they exist
            if not hasattr(self, 'send_button'):
                self.send_button = self.FindName('send_button')
            
            if not hasattr(self, 'user_input'):
                self.user_input = self.FindName('user_input')
            
            if not hasattr(self, 'chat_history'):
                self.chat_history = self.FindName('chat_history')
            
            # Add event handlers
            if self.send_button:
                self.send_button.Click += self.send_message
            
            if self.user_input:
                self.user_input.KeyDown += self.input_key_down
            
        except Exception as e:
            logger.error("Error setting up events: {}".format(e))
    
    def input_key_down(self, sender, e):
        """Handle key down event in user input box."""
        try:
            from System.Windows.Input import Key
            if e.Key == Key.Return and not e.KeyboardDevice.Modifiers:  # Enter without Shift
                e.Handled = True  # Prevent default action
                self.send_message(sender, e)
        except Exception as ex:
            logger.error("Error in input_key_down: {}".format(ex))
    
    def add_message(self, sender, content):
        """Add a message to the chat history."""
        try:
            timestamp = time.strftime("%H:%M:%S")
            message = "[{}] {}: {}".format(timestamp, sender, content)
            self.messages.append(message)
            
            # Update the UI
            chat_text = "\n".join(self.messages)
            self.chat_history.Text = chat_text
            
            # Scroll to bottom
            self.chat_history.ScrollToEnd()
        except Exception as e:
            logger.error("Error adding message: {}".format(e))
    
    def check_server(self):
        """Check if MCP server is running, start if not."""
        try:
            if not mcp_connector.is_mcp_server_running():
                self.add_message("System", "MCP server is not running. Attempting to start...")
                success, message = mcp_connector.start_mcp_server()
                if success:
                    self.add_message("System", "MCP server started successfully.")
                else:
                    self.add_message("System", "Error starting MCP server: {}".format(message))
            else:
                self.add_message("System", "Connected to MCP server on port {}".format(self.mcp_port))
                
            # Try to get server resources to validate connection
            self.test_server_connection()
                
        except Exception as e:
            self.add_message("System", "Error checking server: {}".format(e))
    
    def test_server_connection(self):
        """Test connection to the server by getting resources."""
        try:
            # Create HTTP client
            client = mcp_connector.get_direct_client()
            client.base_url = "http://localhost:{}".format(self.mcp_port)
            
            # Try to get resources
            response = client.get("/api/v1/resources")
            if response.status_code == 200:
                resources = response.json()
                self.add_message("System", "Available resources: {}".format(", ".join(resources)))
            else:
                self.add_message("System", "Connected to server but could not get resources. Status: {}".format(response.status_code))
        except Exception as e:
            self.add_message("System", "Error connecting to MCP server: {}".format(e))
    
    def send_message(self, sender, e):
        """Send a message to the MCP server."""
        try:
            # Get the message text
            message = self.user_input.Text.strip()
            if not message:
                return
                
            # Clear the input box
            self.user_input.Text = ""
            
            # Add message to history
            self.add_message("You", message)
            
            # Process in a separate thread to keep UI responsive
            threading.Thread(target=self.process_message, args=(message,)).Start()
            
        except Exception as e:
            self.add_message("System", "Error sending message: {}".format(e))
    
    def process_message(self, message):
        """Process a message and get response from MCP server."""
        try:
            self.add_message("Revit", "Processing query...")
            
            # Try to get a direct response from the MCP server
            try:
                # Create HTTP client
                client = mcp_connector.get_direct_client()
                client.base_url = "http://localhost:{}".format(self.mcp_port)
                
                # Send the request
                request = {
                    "messages": [{"role": "user", "content": message}],
                    "stream": False,
                    "model": "claude-3-haiku-20240307"
                }
                
                response = client.post("/api/v1/generate", json=request)
                
                if response.status_code == 200:
                    response_data = response.json()
                    if "content" in response_data:
                        self.add_message("Revit", response_data["content"])
                    else:
                        self.add_message("System", "Received empty response from server")
                else:
                    self.add_message("System", "Error from server: {}".format(response.status_code))
                    
            except Exception as direct_err:
                logger.error("Error in direct query processing: {}".format(direct_err))
                self.add_message("System", "Error processing query: {}".format(direct_err))
                
                # Fallback to demo response
                self.add_message("Revit", self.get_demo_response(message))
                
        except Exception as e:
            self.add_message("System", "Error processing message: {}".format(e))
    
    def get_demo_response(self, query):
        """Get a demonstration response based on the query."""
        query_lower = query.lower()
        
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
- ID: 325012, Width: 6'-0", Height: 7'-0"
- ID: 325053, Width: 6'-0", Height: 7'-0"
- ID: 325087, Width: 6'-0", Height: 7'-0"
- ID: 325126, Width: 6'-0", Height: 7'-0"""
            
        elif "model" in query_lower or "info" in query_lower:
            try:
                # Try to get model info using Revit API
                from pyrevit import revit
                doc = revit.doc
                
                # Try to get project info element
                project_info = None
                for element in revit.ElementFilter(doc=doc, of_category="OST_ProjectInformation"):
                    project_info = element
                    break
                
                return "\n".join([
                    "Current Revit Model Information:",
                    "Title: {}".format(doc.Title),
                    "Path: {}".format(doc.PathName),
                    "Project Number: {}".format(project_info.Number if project_info else "N/A"),
                    "Project Name: {}".format(project_info.Name if project_info else "N/A"),
                    "Element Count: {}".format(doc.GetElementCount())
                ])
            except Exception as e:
                logger.error("Error getting model info: {}".format(e))
                return "Error getting model info: {}".format(str(e))
        else:
            return """I'm your Revit assistant. You can ask me about walls, rooms, doors, windows, and other elements in your model. For this demo, I'll respond with sample data."""

def main():
    """Run the MCP Interface."""
    try:
        # Create and show form
        form = MCPInterfaceForm()
        form.Show()
    except Exception as e:
        logger.error("Error in MCP Interface: {}".format(e))
        logger.error(traceback.format_exc())
        forms.alert("Error: {}".format(e), exitscript=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error("Unexpected error: {}".format(e))
        logger.error(traceback.format_exc())
        forms.alert("Unexpected error: {}".format(e), exitscript=True) 