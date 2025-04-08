"""
Chat Interface
"""

__title__ = "Chat"
__doc__ = "Opens the chat interface to interact with the model"

try:
    import os
    import sys
    import json
    import webbrowser
    import requests
    import traceback
    import time
    from pyrevit import script
    from pyrevit import forms
    # Import UI module for running other scripts
    from pyrevit import UI
    
    # Initialize script output
    output = script.get_output()
    output.print_md("# Opening Chat Interface...")
    
    # Add extension lib directory to path
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    lib_dir = os.path.join(script_dir, "lib")
    
    if lib_dir not in sys.path:
        sys.path.append(lib_dir)
    
    # Define fallback settings in case config import fails
    FALLBACK_SETTINGS = {
        "mcp_port": 9876,
        "revit_port": 9877,
        "api_key": "",
        "model": "claude-3-7-sonnet-latest",
        "auto_start_server": True
    }
    
    # Import our utilities - with robust fallback
    settings = None
    try:
        # First try to import config
        from config import load_settings, save_settings
        # If it succeeds, load settings
        settings = load_settings()
    except ImportError:
        output.print_md("### Error: Could not import config module, using defaults")
        settings = FALLBACK_SETTINGS
    except Exception as e:
        output.print_md("### Error loading settings: " + str(e))
        settings = FALLBACK_SETTINGS
    
    # Extra safety check - ensure settings is not None
    if settings is None:
        output.print_md("### Warning: Settings is None, using defaults")
        settings = FALLBACK_SETTINGS
        
    # Get settings values with defaults for safety
    mcp_port = str(settings.get("mcp_port", 9876))
    api_key = settings.get("api_key", "")
    model = settings.get("model", "claude-3-7-sonnet-latest")
    
    output.print_md("### Using MCP port: " + mcp_port)
    
    if not api_key:
        output.print_md("### Warning: API key is not set. Please set it in the settings.")
        result = forms.alert("API key is not set. Do you want to open the settings dialog?", 
                          title="Missing API Key", 
                          options=["Open Settings", "Continue Anyway", "Cancel"])
        
        if result == "Open Settings":
            # Direct approach to open settings
            settings_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                         "Settings.pushbutton", "script.py")
            if os.path.exists(settings_script):
                # Execute the script directly
                output.print_md("### Opening Settings...")
                exec(open(settings_script).read())
            else:
                forms.alert("Settings script not found at: " + settings_script, title="Error")
            script.exit()
        elif result == "Cancel":
            script.exit()
    
    # Check if MCP server is running
    output.print_md("### Checking if MCP server is running on port " + mcp_port + "...")
    
    server_running = False
    max_retries = 5
    retry_count = 0
    
    # Try several times with increasing timeouts
    while not server_running and retry_count < max_retries:
        try:
            timeout = 2 * (retry_count + 1)  # Increase timeout with each retry
            output.print_md("### Attempt " + str(retry_count+1) + "/" + str(max_retries) + " - Timeout: " + str(timeout) + "s")
            
            # Try to connect to the server
            response = requests.get("http://localhost:" + mcp_port + "/ping", timeout=timeout)
            if response.status_code == 200:
                server_running = True
                output.print_md("### MCP server is running!")
                break
            else:
                output.print_md("### Server responded with status code: " + str(response.status_code))
        except requests.exceptions.ConnectionError as ex:
            output.print_md("### Connection failed: " + str(ex).split('(')[0])
        except Exception as ex:
            output.print_md("### Error: " + str(ex))
        
        # Wait before retrying
        retry_count += 1
        if retry_count < max_retries:
            output.print_md("### Waiting " + str(retry_count) + " seconds before retry...")
            time.sleep(retry_count)
    
    # If server is not running after all retries, offer to start it
    if not server_running:
        output.print_md("### MCP server is not running after multiple attempts")
        result = forms.alert("MCP server is not running or not responding. Do you want to start it?", 
                         title="Server Not Running", 
                         options=["Start Server", "Continue Anyway", "Cancel"])
        
        if result == "Start Server":
            # Direct approach to start server
            server_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                      "Start_Server.pushbutton", "script.py")
            if os.path.exists(server_script):
                # Execute the script directly
                output.print_md("### Starting server...")
                exec(open(server_script).read())
                
                # Wait for server to start
                output.print_md("### Server starting. Waiting for it to initialize...")
                retry_count = 0
                server_running = False
                
                while not server_running and retry_count < 10:
                    try:
                        time.sleep(2)  # Wait 2 seconds between checks
                        response = requests.get("http://localhost:" + mcp_port + "/ping", timeout=5)
                        if response.status_code == 200:
                            server_running = True
                            output.print_md("### MCP server is now running!")
                            break
                    except:
                        pass
                    
                    retry_count += 1
                    output.print_md("### Still waiting... (" + str(retry_count) + "/10)")
                
                if not server_running:
                    output.print_md("### Server did not start properly. Please check the server logs.")
                    result = forms.alert("Server did not start properly. Do you want to continue anyway?", 
                                     title="Server Issue", 
                                     options=["Continue Anyway", "Cancel"])
                    if result == "Cancel":
                        script.exit()
            else:
                forms.alert("Start Server script not found at: " + server_script, title="Error")
                script.exit()
        elif result == "Cancel":
            script.exit()
    
    # Create a basic HTML chat interface with directly embedded values instead of using format()
    chat_html = """<!DOCTYPE html>
<html>
<head>
    <title>RevitMCP Chat</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; display: flex; flex-direction: column; height: 100vh; }
        #chat-container { flex: 1; overflow-y: auto; padding: 20px; background-color: #f5f5f5; }
        .user-message { background-color: #e1f5fe; padding: 10px; border-radius: 10px; margin-bottom: 10px; max-width: 80%; align-self: flex-end; margin-left: auto; display: block;}
        .assistant-message { background-color: #ffffff; padding: 10px; border-radius: 10px; margin-bottom: 10px; max-width: 80%; border: 1px solid #e0e0e0; }
        #input-container { display: flex; padding: 10px; background-color: #f0f0f0; border-top: 1px solid #ddd; }
        #user-input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        #send-button { padding: 10px 20px; background-color: #2196F3; color: white; border: none; border-radius: 5px; margin-left: 10px; cursor: pointer; }
        #status { padding: 5px 10px; font-size: 12px; color: #666; }
        .system-message { font-style: italic; color: #555; padding: 5px; text-align: center; }
        .loading { display: inline-block; width: 20px; height: 20px; border: 2px solid #f3f3f3; border-radius: 50%; border-top: 2px solid #3498db; animation: spin 1s linear infinite; margin-left: 10px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        pre { background-color: #f0f0f0; padding: 8px; border-radius: 4px; overflow-x: auto; }
        code { font-family: monospace; background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px; }
    </style>
</head>
<body>
    <div id="chat-container"></div>
    <div id="status">Connected to MCP server on port """ + mcp_port + """</div>
    <div id="input-container">
        <textarea id="user-input" placeholder="Ask about the Revit model..." rows="2" style="resize: vertical;"></textarea>
        <button id="send-button">Send</button>
    </div>
    <script>
        const chatContainer = document.getElementById('chat-container');
        const userInput = document.getElementById('user-input');
        const sendButton = document.getElementById('send-button');
        const statusDiv = document.getElementById('status');
        
        // Server settings
        const serverPort = '""" + mcp_port + """';
        const apiKey = '""" + api_key + """';
        const modelName = '""" + model + """';
        
        // Store message history
        let messages = [];
        
        // Check server connection on load
        fetch('http://localhost:' + serverPort + '/ping', {
            method: 'GET'
        })
            .then(response => response.json())
            .then(data => {
                statusDiv.innerText = "Connected to MCP server on port " + serverPort;
                statusDiv.style.color = "green";
            })
            .catch(error => {
                statusDiv.innerText = "Not connected to MCP server - check server status";
                statusDiv.style.color = "red";
                console.error("Connection error:", error);
            });
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.innerText = text;
            return div.innerHTML;
        }
        
        function formatMessage(text) {
            // Simple Markdown-like formatting
            let html = escapeHtml(text);
            
            // Format code blocks
            html = html.replace(/```([\\s\\S]*?)```/g, '<pre>$1</pre>');
            
            // Format inline code
            html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
            
            // Convert line breaks to <br>
            html = html.replace(/\\n/g, '<br>');
            
            return html;
        }
        
        function addMessage(text, role) {
            const messageDiv = document.createElement('div');
            
            if (role === 'user') {
                messageDiv.className = 'user-message';
                messageDiv.innerHTML = formatMessage(text);
            } else if (role === 'assistant') {
                messageDiv.className = 'assistant-message';
                messageDiv.innerHTML = formatMessage(text);
            } else if (role === 'system') {
                messageDiv.className = 'system-message';
                messageDiv.innerText = text;
            }
            
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        async function sendMessage() {
            const messageText = userInput.value.trim();
            if (!messageText) return;
            
            // Add to UI
            addMessage(messageText, 'user');
            userInput.value = '';
            
            // Add loading indicator
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'system-message';
            loadingDiv.innerHTML = 'Claude is thinking<div class="loading"></div>';
            chatContainer.appendChild(loadingDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            
            // Add to message history
            messages.push({
                role: 'user',
                content: messageText
            });
            
            try {
                const response = await fetch('http://localhost:' + serverPort + '/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        messages: messages,
                        model: modelName
                    })
                });
                
                // Remove loading indicator
                chatContainer.removeChild(loadingDiv);
                
                const data = await response.json();
                
                if (data.content) {
                    // Successful response from Claude API
                    const assistantMessage = data.content;
                    addMessage(assistantMessage, 'assistant');
                    
                    // Add to message history
                    messages.push({
                        role: 'assistant',
                        content: assistantMessage
                    });
                } else if (data.error) {
                    // Error response
                    addMessage('Error: ' + data.error, 'system');
                } else {
                    // Unknown response format
                    addMessage('Received unexpected response from server', 'system');
                    console.error("Unexpected response:", data);
                }
            } catch (error) {
                // Remove loading indicator
                chatContainer.removeChild(loadingDiv);
                
                addMessage('Error connecting to server: ' + error.message, 'system');
                statusDiv.innerText = "Connection lost - check server status";
                statusDiv.style.color = "red";
                console.error("Request error:", error);
            }
        }
        
        sendButton.addEventListener('click', sendMessage);
        userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Initial greeting
        addMessage('Hello! I\\'m Claude, connected to your Revit model. Ask me anything about your model or how I can help.', 'assistant');
    </script>
</body>
</html>"""
    
    # Open the chat interface in the default browser
    output.print_md("### Opening chat interface...")
    
    # Create a temporary HTML file in the user's temp directory
    import tempfile
    import atexit
    
    # Create a temporary file with .html extension
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
    temp_file_path = temp_file.name
    temp_file.close()  # Close the file so we can write to it
    
    # Register a cleanup function to delete the temporary file when the script exits
    def cleanup_temp_file():
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                output.print_md("### Temporary chat file cleaned up.")
        except Exception:
            # Silently ignore cleanup errors
            pass
    
    atexit.register(cleanup_temp_file)
    
    try:
        # Write the HTML content to the temp file
        with open(temp_file_path, 'w') as f:
            f.write(chat_html)
        
        # Open the temp file in the default browser
        webbrowser.open('file://' + temp_file_path)
        
        output.print_md("### Chat interface opened successfully!")
    except Exception as e:
        output.print_md("### Error opening chat interface via file: " + str(e))
        output.print_md("### Trying to connect to server directly...")
        
        # Try connecting directly to the server
        try:
            # Open the server URL directly in the default browser
            server_url = "http://localhost:" + mcp_port + "/"
            webbrowser.open(server_url)
            output.print_md("### Chat interface opened via server!")
        except Exception as e2:
            output.print_md("### Error connecting to server: " + str(e2))
            
            # Last resort fallback: Try using pyRevit's built-in browser
            try:
                output.print_md("### Attempting to open chat interface in pyRevit's output window...")
                output.open_url("http://localhost:" + mcp_port)
                output.print_md("### Please use the pyRevit browser that just opened to chat with the MCP server.")
            except Exception as e3:
                output.print_md("### All connection methods failed: " + str(e3))
                # If all else fails, show an alert
                forms.alert("Failed to open chat interface. Please check the log for details.", 
                         title="Error")
    
except Exception as e:
    import traceback
    print("Error: " + str(e))
    print(traceback.format_exc()) 