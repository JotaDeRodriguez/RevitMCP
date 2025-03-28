"""
MCP Chat Interface for Revit
Provides a rich chat interface for interacting with the Revit model through MCP
"""
import os
import sys
import json
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
    get_server_status,
    log_message
)
from mcp_connector import (
    generate_response,
    load_settings
)

# Set up logging
logger = script.get_logger()

# Chat history storage
CHAT_HISTORY_FILE = os.path.join(SCRIPT_DIR, "chat_history.json")

def load_chat_history():
    """Load chat history from file"""
    if not os.path.exists(CHAT_HISTORY_FILE):
        return []
    
    try:
        with open(CHAT_HISTORY_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Error loading chat history: {}".format(str(e)))
        return []

def save_chat_history(history):
    """Save chat history to file"""
    try:
        with open(CHAT_HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
        return True
    except Exception as e:
        logger.error("Error saving chat history: {}".format(str(e)))
        return False

class ChatMessage:
    """Class representing a chat message"""
    def __init__(self, content, role="user", timestamp=None):
        self.content = content
        self.role = role  # "user" or "assistant"
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            "content": self.content,
            "role": self.role,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        return cls(
            content=data.get("content", ""),
            role=data.get("role", "user"),
            timestamp=data.get("timestamp")
        )

class MCPChatWindow(forms.WPFWindow):
    """Chat window for interacting with the MCP server"""
    
    def __init__(self):
        # Initialize WPF form
        self.xaml_source = os.path.join(SCRIPT_DIR, "ChatWindow.xaml")
        forms.WPFWindow.__init__(self, self.xaml_source)
        
        # Load chat history
        self.chat_history = [ChatMessage.from_dict(msg) for msg in load_chat_history()]
        
        # Set up UI
        self.setup_ui()
        
        # Check server status
        self.check_server_status()
    
    def setup_ui(self):
        """Set up the UI components"""
        # Set window title
        self.Title = "MCP Chat Interface"
        
        # Set up chat history display
        self.refresh_chat_history()
        
        # Set up event handlers
        self.send_button.Click += self.send_message
        self.clear_button.Click += self.clear_chat
        self.query_input.KeyDown += self.on_key_down
        
        # Focus the input field
        self.query_input.Focus()
    
    def check_server_status(self):
        """Check if MCP server is running"""
        try:
            if not is_server_running():
                self.server_status.Text = "Server: Offline"
                self.server_status.Foreground = System.Windows.Media.Brushes.Red
                
                # Ask user if they want to start the server
                result = forms.alert(
                    "MCP Server is not running. Would you like to start it now?",
                    title="Server Offline",
                    yes=True, no=True
                )
                
                if result:
                    # Show progress
                    with forms.ProgressBar(title="Starting MCP Server") as pb:
                        pb.update_progress(10, "Initializing...")
                        
                        # Attempt to start server
                        success = start_server()
                        
                        pb.update_progress(50, "Waiting for server to initialize...")
                        time.sleep(2)  # Give it a moment to start
                        
                        if success:
                            pb.update_progress(100, "Server started successfully!")
                            self.server_status.Text = "Server: Online"
                            self.server_status.Foreground = System.Windows.Media.Brushes.Green
                        else:
                            pb.update_progress(100, "Failed to start server!")
                            forms.alert(
                                "Failed to start MCP Server. See logs for details.",
                                title="Server Start Failed"
                            )
            else:
                self.server_status.Text = "Server: Online"
                self.server_status.Foreground = System.Windows.Media.Brushes.Green
        except Exception as e:
            logger.error("Error checking server status: {}".format(str(e)))
            self.server_status.Text = "Server: Unknown"
            self.server_status.Foreground = System.Windows.Media.Brushes.Orange
    
    def refresh_chat_history(self):
        """Update the chat history display"""
        self.chat_display.Document.Blocks.Clear()
        
        for msg in self.chat_history:
            # Create a new paragraph
            para = System.Windows.Documents.Paragraph()
            
            # Add timestamp
            time_run = System.Windows.Documents.Run("[{}] ".format(msg.timestamp))
            time_run.Foreground = System.Windows.Media.Brushes.Gray
            time_run.FontSize = 10
            para.Inlines.Add(time_run)
            
            # Add role indicator
            if msg.role == "user":
                role_run = System.Windows.Documents.Run("YOU: ")
                role_run.Foreground = System.Windows.Media.Brushes.Blue
                role_run.FontWeight = System.Windows.FontWeights.Bold
            else:
                role_run = System.Windows.Documents.Run("MCP: ")
                role_run.Foreground = System.Windows.Media.Brushes.Green
                role_run.FontWeight = System.Windows.FontWeights.Bold
            para.Inlines.Add(role_run)
            
            # Add message content
            content_run = System.Windows.Documents.Run(msg.content)
            para.Inlines.Add(content_run)
            
            # Add paragraph to document
            self.chat_display.Document.Blocks.Add(para)
        
        # Scroll to the end
        self.chat_display.ScrollToEnd()
    
    def on_key_down(self, sender, args):
        """Handle key press events in the input field"""
        if args.Key == System.Windows.Input.Key.Enter and not System.Windows.Input.Keyboard.Modifiers & System.Windows.Input.ModifierKeys.Shift:
            self.send_message(sender, args)
            args.Handled = True
    
    def send_message(self, sender, args):
        """Send a message to the MCP server"""
        # Get message content
        query = self.query_input.Text.strip()
        if not query:
            return
        
        # Check server status
        if not is_server_running():
            forms.alert(
                "MCP Server is not running. Please start the server first.",
                title="Server Offline"
            )
            return
        
        # Create user message
        user_msg = ChatMessage(query, role="user")
        self.chat_history.append(user_msg)
        
        # Clear input field
        self.query_input.Text = ""
        
        # Update UI
        self.refresh_chat_history()
        
        # Disable input while waiting for response
        self.query_input.IsEnabled = False
        self.send_button.IsEnabled = False
        self.status_text.Text = "Processing query..."
        
        try:
            # Create a progress bar for visual feedback
            with forms.ProgressBar(title="Processing Query") as pb:
                pb.update_progress(10, "Sending query to MCP server...")
                
                # Send query to MCP server
                try:
                    # Generate response from MCP server
                    response_text = generate_response(query)
                    
                    pb.update_progress(90, "Received response!")
                    
                    # Create assistant message
                    assistant_msg = ChatMessage(response_text, role="assistant")
                    self.chat_history.append(assistant_msg)
                    
                    # Save chat history
                    save_chat_history([msg.to_dict() for msg in self.chat_history])
                    
                    # Update UI
                    self.refresh_chat_history()
                    self.status_text.Text = "Ready"
                except Exception as e:
                    logger.error("Error generating response: {}".format(str(e)))
                    logger.error(traceback.format_exc())
                    
                    pb.update_progress(100, "Error")
                    
                    # Create error message
                    error_msg = "Error: {}".format(str(e))
                    assistant_msg = ChatMessage(
                        "I'm sorry, I encountered an error processing your request. Please check the logs for details.",
                        role="assistant"
                    )
                    self.chat_history.append(assistant_msg)
                    
                    # Update UI
                    self.refresh_chat_history()
                    self.status_text.Text = "Error"
                    
                    # Show error message
                    forms.alert(
                        error_msg,
                        title="MCP Error"
                    )
        finally:
            # Re-enable input
            self.query_input.IsEnabled = True
            self.send_button.IsEnabled = True
            self.query_input.Focus()
    
    def clear_chat(self, sender, args):
        """Clear the chat history"""
        result = forms.alert(
            "Are you sure you want to clear the chat history?",
            title="Clear Chat",
            yes=True, no=True
        )
        
        if result:
            self.chat_history = []
            save_chat_history([])
            self.refresh_chat_history()
            self.status_text.Text = "Chat history cleared"

# Main function
def main():
    """Main function to display the chat interface"""
    try:
        # Check platform and Python version
        import platform
        logger.info("Platform: {}".format(platform.platform()))
        logger.info("Python version: {}".format(sys.version))
        
        # Launch the chat window
        chat_window = MCPChatWindow()
        chat_window.ShowDialog()
    except Exception as e:
        logger.error("Error displaying chat window: {}".format(str(e)))
        logger.error(traceback.format_exc())
        forms.alert(
            "Error displaying chat window: {}".format(str(e)),
            title="MCP Chat Error"
        )

if __name__ == "__main__":
    main() 