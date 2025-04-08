"""
Configuration utilities for RevitMCP extension.
Handles reading/writing configuration and managing settings.
"""

import os
import json
import traceback
from pyrevit import script
from pyrevit import forms

# Default settings
DEFAULT_SETTINGS = {
    "mcp_port": 9876,
    "revit_port": 9877,
    "api_key": "",
    "model": "claude-3-7-sonnet-latest",
    "auto_start_server": True
}

# Get the extension directory
EXTENSION_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_FILE = os.path.join(EXTENSION_DIR, "lib", "settings.json")

# Setup logging
logger = script.get_logger()

def load_settings():
    """Load settings from the settings file or return defaults if not found."""
    if not os.path.exists(SETTINGS_FILE):
        logger.debug("Settings file not found, using defaults.")
        return DEFAULT_SETTINGS.copy()
    
    try:
        with open(SETTINGS_FILE, "r") as f:
            loaded = json.load(f)
            # Ensure all keys exist, merging with defaults
            settings = DEFAULT_SETTINGS.copy()
            settings.update(loaded) 
            logger.debug("Settings loaded successfully.")
            return settings
    except Exception as e:
        logger.error("Error loading settings: {}".format(str(e)))
        logger.debug(traceback.format_exc())
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    """Save settings to the settings file."""
    try:
        # Ensure directory exists (Python 2.7 compatible)
        directory = os.path.dirname(SETTINGS_FILE)
        if not os.path.exists(directory):
            try:
                # IronPython 2.7 compatible version (no exist_ok parameter)
                os.makedirs(directory)
            except OSError as e:
                # Handle race condition if directory was created between check and makedirs
                if not os.path.isdir(directory):
                    raise
        
        # Ensure all expected keys are present before saving
        final_settings = DEFAULT_SETTINGS.copy()
        final_settings.update(settings)
        
        with open(SETTINGS_FILE, "w") as f:
            json.dump(final_settings, f, indent=2)
        logger.debug("Settings saved successfully.")
        return True
    except Exception as e:
        logger.error("Error saving settings: {}".format(str(e)))
        logger.debug(traceback.format_exc())
        return False

def get_server_paths():
    """Get paths to the MCP server scripts."""
    server_dir = os.path.join(EXTENSION_DIR, "mcp_server")
    main_script = os.path.join(server_dir, "server.py")
    launcher_script = os.path.join(server_dir, "launcher.bat")
    
    return {
        "server_dir": server_dir,
        "main_script": main_script,
        "launcher_script": launcher_script
    } 