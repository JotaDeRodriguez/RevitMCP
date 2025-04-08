"""
Settings for MCP Server
Allows configuration of ports, API keys, and other settings.
"""

import os
import sys
import traceback
import socket
import time
import threading
from pyrevit import forms
from pyrevit import script

# Add .NET imports for WPF elements
import clr
clr.AddReference("PresentationCore")
clr.AddReference("PresentationFramework")
clr.AddReference("System")
clr.AddReference("System.Net")
from System.Windows.Media import Brushes
from System.Net import WebClient

# Add lib directory to path
script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
lib_dir = os.path.join(script_dir, "lib")
if lib_dir not in sys.path:
    sys.path.append(lib_dir)

# Import our config module
from config import load_settings, save_settings

# Setup logging
logger = script.get_logger()


def check_port_in_use(port):
    """Check if a port is already in use."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0  # If result is 0, port is in use
    except Exception as e:
        logger.debug("Error checking port {}: {}".format(port, e))
        return False


def check_server_status(mcp_port, revit_port):
    """Check if MCP server and Revit RPC server are running."""
    mcp_running = check_port_in_use(mcp_port)
    revit_running = check_port_in_use(revit_port)
    
    return {
        "mcp": mcp_running,
        "revit": revit_running,
        "both_running": mcp_running and revit_running,
        "both_stopped": not mcp_running and not revit_running
    }


def get_server_registry():
    """Get server registry information."""
    registry_file = os.path.join(lib_dir, "server_registry.json")
    if not os.path.exists(registry_file):
        return {"status": "stopped", "pid": None, "mcp_port": None, "revit_port": None}
    
    try:
        import json
        with open(registry_file, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Error reading server registry: {}".format(e))
        return {"status": "unknown", "pid": None, "mcp_port": None, "revit_port": None}


def stop_server(mcp_port):
    """Try to stop the MCP server by sending a shutdown request."""
    try:
        client = WebClient()
        shutdown_url = "http://localhost:{}/shutdown".format(mcp_port)
        client.DownloadString(shutdown_url)
        logger.info("Sent shutdown request to MCP server")
        return True
    except Exception as e:
        logger.error("Failed to stop server: {}".format(e))
        return False


class SettingsForm(forms.WPFWindow):
    """Settings form for RevitMCP."""
    
    def __init__(self):
        xaml_file = os.path.join(os.path.dirname(__file__), "SettingsForm.xaml")
        
        # If XAML file doesn't exist, create a basic one
        if not os.path.exists(xaml_file):
            self._create_default_xaml(xaml_file)
        
        # Initialize the form from XAML
        forms.WPFWindow.__init__(self, xaml_file)
        
        # Load current settings
        self.settings = load_settings()
        self._init_controls()
        
        # Check server status
        self._check_server_status()
        
        # Start server status monitor
        self.status_timer = None
        self._start_status_monitor()
        
        # Set window properties
        self.Title = "RevitMCP Settings"
        
    def _create_default_xaml(self, xaml_file):
        """Create a default XAML file if it doesn't exist."""
        xaml_content = """<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="RevitMCP Settings" Height="500" Width="500"
        WindowStartupLocation="CenterScreen"
        ResizeMode="CanResize"
        Closing="Window_Closing">
    <Grid Margin="10">
        <Grid.RowDefinitions>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="Auto"/>
            <RowDefinition Height="*"/>
            <RowDefinition Height="Auto"/>
        </Grid.RowDefinitions>
        <Grid.ColumnDefinitions>
            <ColumnDefinition Width="120"/>
            <ColumnDefinition Width="*"/>
        </Grid.ColumnDefinitions>
        
        <!-- Server Configuration -->
        <TextBlock Grid.Row="0" Grid.Column="0" Grid.ColumnSpan="2" 
                  Text="Server Configuration" FontWeight="Bold" Margin="0,0,0,10"/>
                  
        <TextBlock Grid.Row="1" Grid.Column="0" Text="MCP Port:" Margin="0,5,10,5" VerticalAlignment="Center"/>
        <TextBox Grid.Row="1" Grid.Column="1" x:Name="mcp_port" Margin="0,5,0,5" Padding="5"/>
        
        <TextBlock Grid.Row="2" Grid.Column="0" Text="Revit Port:" Margin="0,5,10,5" VerticalAlignment="Center"/>
        <TextBox Grid.Row="2" Grid.Column="1" x:Name="revit_port" Margin="0,5,0,5" Padding="5"/>
        
        <CheckBox Grid.Row="3" Grid.Column="1" x:Name="auto_start_server" 
                 Content="Auto-start MCP server when needed" Margin="0,5,0,10"/>
        
        <!-- Server Status -->
        <TextBlock Grid.Row="4" Grid.Column="0" Grid.ColumnSpan="2" 
                  Text="Server Status" FontWeight="Bold" Margin="0,10,0,10"/>
        
        <TextBlock Grid.Row="5" Grid.Column="0" Text="MCP Server:" Margin="0,5,10,5" VerticalAlignment="Center"/>
        <StackPanel Grid.Row="5" Grid.Column="1" Orientation="Horizontal" Margin="0,5,0,5">
            <Border x:Name="mcp_status_indicator" Width="15" Height="15" CornerRadius="7.5" Margin="0,0,5,0" Background="Gray"/>
            <TextBlock x:Name="mcp_status_text" Text="Unknown" VerticalAlignment="Center"/>
        </StackPanel>
        
        <TextBlock Grid.Row="6" Grid.Column="0" Text="Revit RPC:" Margin="0,5,10,5" VerticalAlignment="Center"/>
        <StackPanel Grid.Row="6" Grid.Column="1" Orientation="Horizontal" Margin="0,5,0,5">
            <Border x:Name="revit_status_indicator" Width="15" Height="15" CornerRadius="7.5" Margin="0,0,5,0" Background="Gray"/>
            <TextBlock x:Name="revit_status_text" Text="Unknown" VerticalAlignment="Center"/>
        </StackPanel>
        
        <StackPanel Grid.Row="7" Grid.Column="1" Orientation="Horizontal" Margin="0,5,0,10">
            <Button x:Name="stop_server_button" Content="Stop Server" Width="100" Margin="0,0,10,0" Click="stop_server_Click"/>
            <Button x:Name="restart_server_button" Content="Restart Server" Width="100" Click="restart_server_Click"/>
        </StackPanel>
        
        <!-- API Configuration -->
        <TextBlock Grid.Row="8" Grid.Column="0" Grid.ColumnSpan="2" 
                  Text="AI Configuration" FontWeight="Bold" Margin="0,10,0,10"/>
                  
        <TextBlock Grid.Row="9" Grid.Column="0" Text="API Key:" Margin="0,5,10,5" VerticalAlignment="Center"/>
        <TextBox Grid.Row="9" Grid.Column="1" x:Name="api_key" Margin="0,5,0,5" Padding="5"/>
        
        <TextBlock Grid.Row="10" Grid.Column="0" Text="Model:" Margin="0,5,10,5" VerticalAlignment="Center"/>
        <ComboBox Grid.Row="10" Grid.Column="1" x:Name="model" Margin="0,5,0,5" Padding="5">
            <ComboBoxItem Content="claude-3-5-sonnet-20240620"/>
            <ComboBoxItem Content="claude-3-opus-20240229"/>
            <ComboBoxItem Content="claude-3-7-sonnet-latest"/>
        </ComboBox>
        
        <!-- Buttons -->
        <StackPanel Grid.Row="11" Grid.Column="0" Grid.ColumnSpan="2" 
                   Orientation="Horizontal" HorizontalAlignment="Right" Margin="0,10,0,0">
            <Button x:Name="save_button" Content="Save" Width="80" Margin="0,0,10,0" Click="save_button_Click"/>
            <Button x:Name="cancel_button" Content="Cancel" Width="80" Click="cancel_button_Click"/>
        </StackPanel>
    </Grid>
</Window>
"""
        try:
            with open(xaml_file, "w") as f:
                f.write(xaml_content)
        except Exception as e:
            logger.error("Failed to create default XAML file: {}".format(e))
    
    def _init_controls(self):
        """Initialize form controls with current settings."""
        try:
            # Set port values
            self.mcp_port.Text = str(self.settings.get("mcp_port", 9876))
            self.revit_port.Text = str(self.settings.get("revit_port", 9877))
            
            # Set auto-start checkbox
            self.auto_start_server.IsChecked = self.settings.get("auto_start_server", True)
            
            # Set API key and model
            self.api_key.Text = self.settings.get("api_key", "")
            
            # Set model dropdown
            model_value = self.settings.get("model", "claude-3-7-sonnet-latest")
            
            # Find and select the matching model in the dropdown
            for item in self.model.Items:
                if item.Content == model_value:
                    self.model.SelectedItem = item
                    break
                    
            # Default to first item if not found
            if self.model.SelectedItem is None and self.model.Items.Count > 0:
                self.model.SelectedIndex = 0
                
        except Exception as e:
            logger.error("Error initializing settings form: {}".format(e))
            logger.debug(traceback.format_exc())
    
    def _check_server_status(self):
        """Check and update server status indicators."""
        try:
            mcp_port = int(self.mcp_port.Text)
            revit_port = int(self.revit_port.Text)
            
            status = check_server_status(mcp_port, revit_port)
            
            # Update MCP status
            if status["mcp"]:
                self.mcp_status_indicator.Background = Brushes.Green
                self.mcp_status_text.Text = "Running"
            else:
                self.mcp_status_indicator.Background = Brushes.Red
                self.mcp_status_text.Text = "Stopped"
                
            # Update Revit status
            if status["revit"]:
                self.revit_status_indicator.Background = Brushes.Green
                self.revit_status_text.Text = "Running"
            else:
                self.revit_status_indicator.Background = Brushes.Red
                self.revit_status_text.Text = "Stopped"
                
            # Update buttons
            self.stop_server_button.IsEnabled = status["mcp"] or status["revit"]
            self.restart_server_button.IsEnabled = status["mcp"] or status["revit"]
            
        except Exception as e:
            logger.error("Error checking server status: {}".format(e))
            logger.debug(traceback.format_exc())
    
    def _start_status_monitor(self):
        """Start a timer to periodically update server status."""
        def update_status():
            try:
                if self.IsLoaded:
                    self.Dispatcher.Invoke(lambda: self._check_server_status())
                    # Schedule next update if window is still open
                    if self.IsLoaded:
                        self.status_timer = threading.Timer(2.0, update_status)
                        self.status_timer.daemon = True
                        self.status_timer.start()
            except Exception as e:
                logger.debug("Error in status monitor: {}".format(e))
                
        # Start first update
        self.status_timer = threading.Timer(2.0, update_status)
        self.status_timer.daemon = True
        self.status_timer.start()
    
    def save_button_Click(self, sender, e):
        """Save settings and close the form."""
        try:
            # Validate port numbers
            try:
                mcp_port = int(self.mcp_port.Text)
                revit_port = int(self.revit_port.Text)
                
                if not (1024 <= mcp_port <= 65535) or not (1024 <= revit_port <= 65535):
                    forms.alert("Ports must be between 1024 and 65535", title="Invalid Ports")
                    return
                    
                if mcp_port == revit_port:
                    forms.alert("MCP port and Revit port must be different", title="Invalid Ports")
                    return
                    
            except ValueError:
                forms.alert("Ports must be valid integers", title="Invalid Ports")
                return
            
            # Get model value
            model_value = "claude-3-7-sonnet-latest"  # Default
            if self.model.SelectedItem is not None:
                model_value = self.model.SelectedItem.Content
            
            # Update settings
            self.settings.update({
                "mcp_port": mcp_port,
                "revit_port": revit_port,
                "auto_start_server": self.auto_start_server.IsChecked,
                "api_key": self.api_key.Text,
                "model": model_value
            })
            
            # Save settings to file
            if save_settings(self.settings):
                logger.info("Settings saved successfully")
                self.Close()
            else:
                forms.alert("Failed to save settings", title="Error")
                
        except Exception as e:
            logger.error("Error saving settings: {}".format(e))
            logger.debug(traceback.format_exc())
            forms.alert("An error occurred: {}".format(e), title="Error")
    
    def cancel_button_Click(self, sender, e):
        """Close the form without saving."""
        self.Close()
    
    def stop_server_Click(self, sender, e):
        """Stop the running server."""
        try:
            mcp_port = int(self.mcp_port.Text)
            registry = get_server_registry()
            
            if stop_server(mcp_port):
                forms.alert("Server shutdown request sent. This may take a moment.", title="Server Stopping")
                # Wait a moment and update status
                threading.Timer(2.0, self._check_server_status).start()
            else:
                forms.alert("Failed to stop server. You may need to stop it manually.", title="Error")
                
        except Exception as e:
            logger.error("Error stopping server: {}".format(e))
            forms.alert("Error stopping server: {}".format(e), title="Error")
    
    def restart_server_Click(self, sender, e):
        """Restart the server."""
        try:
            mcp_port = int(self.mcp_port.Text)
            
            # First stop the server
            if stop_server(mcp_port):
                forms.alert("Server shutdown request sent. The server will be restarted from the Start Server button.", 
                           title="Server Restarting")
                
                # Wait for shutdown
                threading.Timer(2.0, self._check_server_status).start()
                
                # Let the user know they need to press Start Server
                forms.alert("Please use the Start Server button to restart the server after it has fully shutdown.", 
                           title="Manual Restart Required")
            else:
                forms.alert("Failed to stop server. You may need to stop it manually.", title="Error")
                
        except Exception as e:
            logger.error("Error restarting server: {}".format(e))
            forms.alert("Error restarting server: {}".format(e), title="Error")
    
    def Window_Closing(self, sender, e):
        """Handle window closing events."""
        # Stop the status monitor
        if self.status_timer:
            self.status_timer.cancel()


# Main execution
if __name__ == "__main__":
    try:
        form = SettingsForm()
        form.ShowDialog()
    except Exception as e:
        logger.error("Error launching settings form: {}".format(e))
        logger.debug(traceback.format_exc())
        forms.alert("Error launching settings: {}".format(str(e)), title="Error") 