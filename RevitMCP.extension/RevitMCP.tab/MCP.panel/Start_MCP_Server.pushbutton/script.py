"""Toggle the MCP server on/off."""

import os
import sys
import traceback
import threading
from pyrevit import forms
from pyrevit import script

# Setup logging
logger = script.get_logger()
logger.info("Start/Stop MCP Server button clicked")

try:
    # Add lib directory to path
    script_dir = os.path.dirname(os.path.dirname(__file__))
    lib_dir = os.path.join(script_dir, "lib")
    sys.path.append(lib_dir)
    
    # Add server directory to path
    server_dir = os.path.join(script_dir, "server")
    sys.path.append(server_dir)

    # Import MCP connector
    try:
        import mcp_connector
    except ImportError:
        forms.alert("Error: Could not import mcp_connector module. Make sure all required files are in the lib directory.", exitscript=True)
        sys.exit(1)

    def open_test_interface():
        """Open the MCP Interface window."""
        try:
            # Delay slightly to ensure server is running
            import time
            time.sleep(1)
            
            # Get the path to the MCP Interface script
            mcp_interface_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "MCP_Interface.pushbutton")
            logger.info("MCP Interface directory: {}".format(mcp_interface_dir))
            
            # Method 1: Try using direct method call
            try:
                logger.info("Trying to import and run MCP Interface directly")
                # Add to path
                if mcp_interface_dir not in sys.path:
                    sys.path.append(mcp_interface_dir)
                
                # Import and run main function from MCP Interface
                import script
                script.main()
                logger.info("MCP Interface opened directly via import")
                return True
            except Exception as e:
                logger.error("Error importing MCP Interface directly: {}".format(e))
            
            # Method 2: Try running as separate command
            try:
                logger.info("Trying to run MCP Interface via PyRevit command")
                from pyrevit import script as pyscript
                from pyrevit.coreutils import ribbon
                
                # Find the MCP Interface button in the ribbon
                button = ribbon.find_button_command('RevitMCP.tab', 'MCP_Interface')
                
                if button:
                    # Invoke the button command
                    button.invoke()
                    logger.info("MCP Interface opened via button invoke")
                    return True
                else:
                    logger.warning("Could not find MCP Interface button in ribbon")
            except Exception as e:
                logger.error("Error invoking MCP Interface button: {}".format(e))
            
            # Method 3: Last resort - just tell the user to open it manually
            logger.info("Displaying manual instruction to open MCP Interface")
            forms.alert("MCP server is running. Please click on the MCP Interface button to open the chat window.", exitscript=False)
            return False
            
        except Exception as e:
            logger.error("Error opening MCP Interface: {}".format(e))
            return False

    # Check if server is running
    if mcp_connector.is_mcp_server_running():
        # Ask for confirmation before stopping
        if forms.alert("MCP server is currently running. Do you want to stop it?", 
                     yes=True, no=True, ok=False):
            logger.info("User confirmed stopping the MCP server")
            success, message = mcp_connector.stop_mcp_server()
            if success:
                forms.alert("MCP server stopped successfully.", exitscript=False)
            else:
                forms.alert("Error stopping MCP server: {}".format(message), exitscript=True)
        else:
            logger.info("User cancelled stopping the MCP server")
    else:
        # Ask for confirmation before starting
        if forms.alert("MCP server is not running. Do you want to start it?", 
                     yes=True, no=True, ok=False):
            logger.info("User confirmed starting the MCP server")
            
            # Check if server directory exists
            if not os.path.exists(server_dir):
                # Create server directory
                try:
                    os.makedirs(server_dir)
                    logger.info("Created server directory at {}".format(server_dir))
                except:
                    forms.alert("Error: Could not create server directory at {}. Please create it manually.".format(server_dir), exitscript=True)
                    sys.exit(1)
            
            # Check if the RevitAPIServer module exists
            revit_api_server_path = os.path.join(server_dir, "revit_api_server.py")
            if not os.path.exists(revit_api_server_path):
                forms.alert("Error: Could not import RevitAPIServer module. Make sure all required files are in the server directory.", exitscript=True)
                sys.exit(1)
            
            # Start the server
            success, message = mcp_connector.start_mcp_server()
            if success:
                forms.alert("MCP server started successfully. Opening MCP Interface.", exitscript=False)
                
                # Open the MCP Interface in a separate thread to avoid blocking
                threading.Thread(target=open_test_interface).start()
            else:
                forms.alert("Error starting MCP server: {}".format(message), exitscript=True)
        else:
            logger.info("User cancelled starting the MCP server")

except Exception as e:
    error_msg = "Unexpected error: {}\n{}".format(str(e), traceback.format_exc())
    logger.error(error_msg)
    forms.alert("Error in Start/Stop MCP Server button: {}".format(str(e)), exitscript=True) 