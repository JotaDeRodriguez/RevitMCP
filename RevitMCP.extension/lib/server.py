@app.get("/ping")
def ping():
    """Simple endpoint to check if server is running"""
    return {"status": "success", "message": "MCP server is running"}

@app.post("/chat")
def chat(request: dict):
    """Process a chat request and return a response from Claude"""
    prompt = request.get("prompt")
    api_key = request.get("api_key")
    
    if not prompt:
        return {"status": "error", "detail": "No prompt provided"}
    
    # For debugging - just return a test response
    return {
        "status": "success",
        "response": "This is a test response from the MCP server. Your prompt was: " + prompt
    }
    
    # Once the connection is working, uncomment this real implementation:
    """
    if not api_key:
        return {"status": "error", "detail": "No API key provided"}
    
    try:
        # Call Claude API with the prompt
        import anthropic
        
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model="claude-3-7-sonnet-latest",
            max_tokens=2000,
            system="You are an assistant that helps with Revit models. Answer questions about the model and provide insights.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return {
            "status": "success",
            "response": message.content[0].text
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}
    """ 