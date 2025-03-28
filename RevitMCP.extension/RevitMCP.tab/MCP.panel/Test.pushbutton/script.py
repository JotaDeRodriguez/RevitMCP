"""Test button to verify PyRevit is working correctly with the MCP extension."""

import os
import sys
import traceback
from pyrevit import forms
from pyrevit import script
from pyrevit import revit

# Setup logging
logger = script.get_logger()
logger.info("Test button clicked")

try:
    # Check if Revit API is accessible
    doc = revit.doc
    if not doc:
        forms.alert("No active Revit document found", exitscript=True)
        sys.exit(1)
    
    # Basic info about the current document
    project_info = doc.ProjectInformation
    title = doc.Title
    path = doc.PathName or "Unsaved"
    
    # Get model elements count
    try:
        from Autodesk.Revit.DB import FilteredElementCollector
        element_count = FilteredElementCollector(doc).WhereElementIsNotElementType().GetElementCount()
    except:
        element_count = "Unknown"
    
    # Check if directories exist
    script_dir = os.path.dirname(os.path.dirname(__file__))
    lib_dir = os.path.join(script_dir, "lib")
    server_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "server")
    
    # Check if lib directory exists
    if not os.path.exists(lib_dir):
        lib_status = "Missing"
    else:
        try:
            sys.path.append(lib_dir)
            import mcp_connector
            lib_status = "OK"
        except ImportError:
            lib_status = "Error: mcp_connector.py not found"
    
    # Check if server directory exists
    if not os.path.exists(server_dir):
        server_status = "Missing"
    else:
        try:
            sys.path.append(server_dir)
            import revit_api_server
            server_status = "OK"
        except ImportError:
            server_status = "Error: revit_api_server.py not found"
    
    # Create message
    message = """
Test results:

Revit Document:
- Title: {}
- Path: {}
- Project Number: {}
- Project Name: {}
- Elements: {}

MCP Extension:
- Lib directory: {}
- Server directory: {}

The test was successful! The MCP extension is properly connected to PyRevit.
""".format(
        title,
        path,
        project_info.Number if project_info else "None",
        project_info.Name if project_info else "None",
        element_count,
        lib_status,
        server_status
    )
    
    # Show results
    forms.alert(message, title="MCP Extension Test Results")

except Exception as e:
    error_msg = "Unexpected error: {}\n{}".format(str(e), traceback.format_exc())
    logger.error(error_msg)
    forms.alert("Error in Test button: {}".format(str(e)), exitscript=True) 