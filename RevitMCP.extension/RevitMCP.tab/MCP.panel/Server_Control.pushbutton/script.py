"""
MCP Server Controller
Provides UI for managing the MCP server
"""
import os
import sys
import subprocess
import threading
import time
import traceback
from datetime import datetime

# Add lib directory to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(os.path.dirname(os.path.dirname(SCRIPT_DIR)), "lib")
if LIB_DIR not in sys.path:
    sys.path.append(LIB_DIR)

# PyRevit imports
from pyrevit import forms
from pyrevit import script

# MCP imports
from server_registry import (
    is_server_running,
    start_server, 
    stop_server, 
    get_server_status,
    get_server_url,
    log_message
)

# Set up logging
logger = script.get_logger()

# Log paths
SERVER_DIR = os.path.join(os.path.dirname(os.path.dirname(SCRIPT_DIR)), "server")
LOG_FILE = os.path.join(SERVER_DIR, "server_log.txt")

class ServerControlForm(forms.WPFWindow):
    """Form for controlling the MCP server"""
    
    def __init__(self):
        # Load UI
        forms.WPFWindow.__init__(self, os.path.join(SCRIPT_DIR, "ServerControl.xaml"))
        
        # Set up event handlers
        self.start_button.Click += self.start_server
        self.stop_button.Click += self.stop_server
        self.refresh_button.Click += self.refresh_status
        self.view_logs_button.Click += self.view_logs
        
        # Initialize with current status
        self.refresh_status(None, None)
    
    def start_server(self, sender, args):
        """Start the MCP server"""
        self.status_text.Text = "Starting server..."
        self.start_button.IsEnabled = False
        self.stop_button.IsEnabled = False
        self.refresh_button.IsEnabled = False
        
        # Start in a separate thread to keep UI responsive
        def start_thread():
            try:
                # Create progress bar in UI thread
                self.Dispatcher.Invoke(lambda: forms.ProgressBar.show_progress(1, 10, "Starting server..."))
                
                # Start server
                success = start_server()
                
                # Update UI in UI thread
                if success:
                    self.Dispatcher.Invoke(lambda: forms.ProgressBar.update_progress(10, 10, "Server started successfully"))
                    self.Dispatcher.Invoke(lambda: self.refresh_status(None, None))
                    time.sleep(1)
                    self.Dispatcher.Invoke(lambda: forms.ProgressBar.hide_progress())
                else:
                    self.Dispatcher.Invoke(lambda: forms.ProgressBar.update_progress(10, 10, "Failed to start server"))
                    self.Dispatcher.Invoke(lambda: forms.alert("Failed to start MCP server. Check logs for details.", title="Server Error"))
                    self.Dispatcher.Invoke(lambda: self.refresh_status(None, None))
                    time.sleep(1)
                    self.Dispatcher.Invoke(lambda: forms.ProgressBar.hide_progress())
            except Exception as e:
                logger.error("Error starting server: {}".format(str(e)))
                logger.error(traceback.format_exc())
                
                self.Dispatcher.Invoke(lambda: forms.ProgressBar.hide_progress())
                self.Dispatcher.Invoke(lambda: forms.alert("Error starting server: {}".format(str(e)), title="Server Error"))
                self.Dispatcher.Invoke(lambda: self.refresh_status(None, None))
        
        # Start thread
        threading.Thread(target=start_thread).start()
    
    def stop_server(self, sender, args):
        """Stop the MCP server"""
        self.status_text.Text = "Stopping server..."
        self.start_button.IsEnabled = False
        self.stop_button.IsEnabled = False
        self.refresh_button.IsEnabled = False
        
        # Stop in a separate thread to keep UI responsive
        def stop_thread():
            try:
                # Show progress in UI thread
                self.Dispatcher.Invoke(lambda: forms.ProgressBar.show_progress(1, 10, "Stopping server..."))
                
                # Stop server
                success = stop_server()
                
                # Update UI in UI thread
                if success:
                    self.Dispatcher.Invoke(lambda: forms.ProgressBar.update_progress(10, 10, "Server stopped successfully"))
                    self.Dispatcher.Invoke(lambda: self.refresh_status(None, None))
                    time.sleep(1)
                    self.Dispatcher.Invoke(lambda: forms.ProgressBar.hide_progress())
                else:
                    self.Dispatcher.Invoke(lambda: forms.ProgressBar.update_progress(10, 10, "Failed to stop server"))
                    self.Dispatcher.Invoke(lambda: forms.alert("Failed to stop MCP server. Check logs for details.", title="Server Error"))
                    self.Dispatcher.Invoke(lambda: self.refresh_status(None, None))
                    time.sleep(1)
                    self.Dispatcher.Invoke(lambda: forms.ProgressBar.hide_progress())
            except Exception as e:
                logger.error("Error stopping server: {}".format(str(e)))
                logger.error(traceback.format_exc())
                
                self.Dispatcher.Invoke(lambda: forms.ProgressBar.hide_progress())
                self.Dispatcher.Invoke(lambda: forms.alert("Error stopping server: {}".format(str(e)), title="Server Error"))
                self.Dispatcher.Invoke(lambda: self.refresh_status(None, None))
        
        # Start thread
        threading.Thread(target=stop_thread).start()
    
    def refresh_status(self, sender, args):
        """Refresh the server status display"""
        try:
            # Get server status
            running = is_server_running()
            
            # Update UI based on status
            if running:
                self.status_text.Text = "Running"
                self.status_indicator.Fill = System.Windows.Media.Brushes.Green
                self.start_button.IsEnabled = False
                self.stop_button.IsEnabled = True
                
                # Get server URL
                server_url = get_server_url()
                self.url_text.Text = server_url
            else:
                self.status_text.Text = "Stopped"
                self.status_indicator.Fill = System.Windows.Media.Brushes.Red
                self.start_button.IsEnabled = True
                self.stop_button.IsEnabled = False
                self.url_text.Text = "Not available"
            
            # Get detailed status
            status = get_server_status()
            
            # Update additional info
            self.mcp_port_text.Text = str(status.get("mcp_port", "N/A"))
            self.revit_port_text.Text = str(status.get("revit_port", "N/A"))
            self.last_update_text.Text = status.get("last_update", "Never")
            
            # Enable refresh button
            self.refresh_button.IsEnabled = True
            
        except Exception as e:
            logger.error("Error refreshing status: {}".format(str(e)))
            logger.error(traceback.format_exc())
            
            # Show error
            self.status_text.Text = "Error"
            self.status_indicator.Fill = System.Windows.Media.Brushes.Orange
            self.start_button.IsEnabled = True
            self.stop_button.IsEnabled = False
            self.url_text.Text = "Not available"
            self.refresh_button.IsEnabled = True
    
    def view_logs(self, sender, args):
        """View server logs"""
        try:
            # Check if log file exists
            if not os.path.exists(LOG_FILE):
                forms.alert("Log file not found.", title="View Logs")
                return
            
            # Read log file
            with open(LOG_FILE, "r") as f:
                log_content = f.read()
            
            # Get the last 100 lines (or fewer if file is smaller)
            log_lines = log_content.splitlines()
            if len(log_lines) > 100:
                log_lines = log_lines[-100:]
                log_content = "\n".join(log_lines)
                log_content = "... (showing last 100 lines) ...\n\n" + log_content
            
            # Create log viewer window
            log_window = forms.TextInputForm(
                title="MCP Server Logs",
                width=800,
                height=600,
                default=log_content,
                readonly=True
            )
            
            log_window.show()
            
        except Exception as e:
            logger.error("Error viewing logs: {}".format(str(e)))
            logger.error(traceback.format_exc())
            
            forms.alert("Error viewing logs: {}".format(str(e)), title="View Logs")

def main():
    """Display the server control form"""
    try:
        # Display the form
        server_control = ServerControlForm()
        server_control.ShowDialog()
    except Exception as e:
        logger.error("Error displaying server control: {}".format(str(e)))
        logger.error(traceback.format_exc())
        
        forms.alert("Error displaying server control: {}".format(str(e)), title="Server Control Error")

if __name__ == "__main__":
    main() 