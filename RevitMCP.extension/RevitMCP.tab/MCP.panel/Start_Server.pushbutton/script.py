"""
Start MCP Server
"""

__title__ = "Start Server"
__doc__ = "Starts the MCP server"

try:
    import os
    import sys
    import subprocess
    import json
    import traceback
    import time
    import threading
    
    from pyrevit import script
    from pyrevit import forms
    
    # Initialize script output
    output = script.get_output()
    output.print_md("# Starting MCP Server...")
    
    # Add extension lib directory to path
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    lib_dir = os.path.join(script_dir, "lib")
    
    if lib_dir not in sys.path:
        sys.path.append(lib_dir)
    
    # Import our utilities
    try:
        from config import load_settings, save_settings, get_server_paths
    except ImportError:
        output.print_md("### Error: Could not import config module")
        raise
    
    # Load settings
    settings = load_settings()
    mcp_port = settings.get("mcp_port", 9876)
    revit_port = settings.get("revit_port", 9877)
    api_key = settings.get("api_key", "")
    model = settings.get("model", "claude-3-7-sonnet-latest")
    
    # Get server paths
    paths = get_server_paths()
    server_dir = paths.get("server_dir")
    launcher_script = paths.get("launcher_script")
    
    output.print_md("### Server Information")
    output.print_md("- MCP Port: {}".format(mcp_port))
    output.print_md("- Revit Port: {}".format(revit_port))
    output.print_md("- Model: {}".format(model))
    output.print_md("- API Key: {}".format("*" * 8 if api_key else "Not set"))
    output.print_md("- Server Directory: {}".format(server_dir))
    output.print_md("- Launcher Script: {}".format(launcher_script))
    
    # Check if server files exist
    if not os.path.exists(launcher_script):
        output.print_md("### Error: Server launcher not found!")
        forms.alert("MCP server launcher not found at: {}".format(launcher_script), title="Missing Server Files")
        script.exit()
    
    # Start the server process
    try:
        output.print_md("### Starting MCP server process...")
        
        # Run the terminal visibly (no startupinfo)
        cmd = [launcher_script, str(mcp_port), str(revit_port), model, api_key]
        
        # Start the launcher with visible console window
        process = subprocess.Popen(
            cmd,
            cwd=server_dir,
            # No startupinfo here to keep the window visible
            creationflags=subprocess.CREATE_NEW_CONSOLE  # This creates a new visible console window
        )
        
        output.print_md("### MCP server started with PID: {}".format(process.pid))
        output.print_md("### Waiting for server to initialize...")
        
        # Wait a moment for server to initialize
        time.sleep(2)
        
        output.print_md("### Server started successfully!")
        forms.alert("MCP server started successfully on port {}! Check the console window for details.".format(mcp_port), title="Server Started")
        
    except Exception as e:
        output.print_md("### Error starting MCP server: {}".format(e))
        forms.alert("Failed to start MCP server: {}".format(e), title="Error")
    
except Exception as e:
    import traceback
    print("Error: " + str(e))
    print(traceback.format_exc())
