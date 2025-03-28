"""
MCP Settings UI
Provides an interface for configuring the MCP server
"""
import os
import sys
import json
import traceback

# Add lib directory to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(os.path.dirname(os.path.dirname(SCRIPT_DIR)), "lib")
if LIB_DIR not in sys.path:
    sys.path.append(LIB_DIR)

# PyRevit imports
from pyrevit import forms
from pyrevit import script

# Import MCP connector
try:
    from server_registry import log_message
    import mcp_connector
except ImportError as e:
    error_msg = "Error: Could not import MCP modules. Make sure all required files are in the lib directory."
    script.get_logger().error("{}: {}".format(error_msg, str(e)))
    forms.alert(error_msg, exitscript=True)
    sys.exit(1)

# Set up logging
logger = script.get_logger()

def show_settings_dialog():
    """Display settings dialog and allow configuration"""
    try:
        # Get current settings
        current_settings = mcp_connector.load_settings()
        
        # Create a single string prompt for all settings
        settings_prompt = """Enter values for MCP settings.
Current values are shown in [brackets].
Separate each value with a comma.

Format: MCP Port, Revit Port, API Key, Model Name, Auto-start(Yes/No)

Current Values:
MCP Port: [{}]
Revit Port: [{}]
API Key: [{}]
Model: [{}]
Auto-start: [{}]

Example: 9876,9877,your_api_key,claude-3-7-sonnet-20250219,Yes
""".format(
            current_settings.get("mcp_port", 9876),
            current_settings.get("revit_port", 9877),
            current_settings.get("api_key", ""),
            current_settings.get("model", "claude-3-7-sonnet-20250219"),
            "Yes" if current_settings.get("auto_start_server", True) else "No"
        )
        
        # Create a default input string with current values
        default_input = "{},{},{},{},{}".format(
            current_settings.get("mcp_port", 9876),
            current_settings.get("revit_port", 9877),
            current_settings.get("api_key", ""),
            current_settings.get("model", "claude-3-7-sonnet-20250219"),
            "Yes" if current_settings.get("auto_start_server", True) else "No"
        )
        
        # Get user input
        user_input = forms.ask_for_string(
            prompt=settings_prompt,
            title="MCP Settings",
            default=default_input
        )
        
        # If user cancelled, return
        if user_input is None:
            return
            
        # Parse user input
        parts = user_input.split(',')
        if len(parts) < 5:
            forms.alert("Invalid input format. Please use: mcp_port,revit_port,api_key,model,auto_start", title="Settings Error")
            return
            
        # Extract values
        mcp_port, revit_port, api_key, model, auto_start = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip(), parts[4].strip()
        
        # Prepare new settings
        new_settings = current_settings.copy()
        
        # Update ports (validate as integers)
        try:
            new_settings["mcp_port"] = int(mcp_port)
        except ValueError:
            forms.alert("Invalid MCP port - must be a number. Using default value.", title="Settings Error")
            new_settings["mcp_port"] = 9876
            
        try:
            new_settings["revit_port"] = int(revit_port)
        except ValueError:
            forms.alert("Invalid Revit port - must be a number. Using default value.", title="Settings Error")
            new_settings["revit_port"] = 9877
        
        # Update other settings
        new_settings["api_key"] = api_key
        new_settings["model"] = model
        new_settings["auto_start_server"] = auto_start.lower() in ('yes', 'true', 'y', '1', 'on')
        
        # Show confirmation
        confirm_settings_text = """Save these settings?

MCP Port: {}
Revit Port: {}
API Key: {}
Model: {}
Auto-start: {}""".format(
            new_settings.get("mcp_port", 9876),
            new_settings.get("revit_port", 9877),
            new_settings.get("api_key", ""),
            new_settings.get("model", "claude-3-7-sonnet-20250219"),
            "Yes" if new_settings.get("auto_start_server", True) else "No"
        )
        
        if forms.alert(confirm_settings_text, title="Confirm Settings", yes=True, no=True):
            # Save settings
            if mcp_connector.save_settings(new_settings):
                forms.alert("Settings saved successfully", title="Settings")
            else:
                forms.alert("Failed to save settings", title="Settings Error")
                
    except Exception as e:
        logger.error("Error in settings UI: {}".format(str(e)))
        logger.error(traceback.format_exc())
        forms.alert("Error: {}".format(str(e)), title="Settings Error")

if __name__ == "__main__":
    show_settings_dialog() 