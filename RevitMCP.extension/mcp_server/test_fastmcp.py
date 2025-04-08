"""
Test script to check FastMCP API
"""

try:
    print("Trying to import MCP...")
    import mcp
    print(f"MCP version: {mcp.__version__}")
    
    print("\nTrying to import FastMCP...")
    try:
        # Try to import from fastmcp package
        import fastmcp
        from fastmcp import FastMCP
        print("Successfully imported FastMCP from fastmcp package")
        print(f"FastMCP package: {fastmcp.__file__}")
    except ImportError:
        # Try to import from mcp.server.fastmcp
        print("Couldn't import from fastmcp package, trying mcp.server.fastmcp...")
        from mcp.server.fastmcp import FastMCP
        print("Successfully imported FastMCP from mcp.server.fastmcp")
    
    # Create a FastAPI instance
    from fastapi import FastAPI
    app = FastAPI()
    
    # Create FastMCP instance
    print("\nTrying to create FastMCP instance...")
    try:
        # First try with app parameter
        mcp_server = FastMCP(title="Test MCP Server", app=app)
        print("Created FastMCP with app parameter")
    except Exception as e:
        print(f"Error creating FastMCP with app parameter: {e}")
        
        try:
            # Try without app parameter
            mcp_server = FastMCP(title="Test MCP Server")
            print("Created FastMCP without app parameter")
        except Exception as e:
            print(f"Error creating FastMCP without app parameter: {e}")
    
    # Check available methods
    print("\nChecking FastMCP methods:")
    methods = [attr for attr in dir(mcp_server) if not attr.startswith('_')]
    for method in methods:
        print(f"- {method}")
    
    print("\nFastMCP API exploration completed")
    
except Exception as e:
    print(f"Error: {e}") 