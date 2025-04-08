"""
Diagnostic script to check MCP module structure
"""

import sys
import inspect

def inspect_module(module, indent=0):
    """Recursively inspect a module and its attributes."""
    prefix = "  " * indent
    print(f"{prefix}Module: {module.__name__}")
    
    # Get all attributes that don't start with underscore
    attrs = [attr for attr in dir(module) if not attr.startswith('_')]
    
    for attr_name in attrs:
        try:
            attr = getattr(module, attr_name)
            if inspect.ismodule(attr):
                # Recursively inspect submodules
                if attr.__name__.startswith(module.__name__):
                    print(f"{prefix}  Submodule: {attr_name}")
                    inspect_module(attr, indent + 1)
                else:
                    print(f"{prefix}  External module: {attr_name} ({attr.__name__})")
            elif inspect.isclass(attr):
                print(f"{prefix}  Class: {attr_name}")
                # List a few methods of the class
                class_methods = [m for m in dir(attr) if not m.startswith('_')][:5]
                if class_methods:
                    print(f"{prefix}    Methods: {', '.join(class_methods)}")
            elif inspect.isfunction(attr):
                print(f"{prefix}  Function: {attr_name}")
            else:
                value_str = str(attr)
                if len(value_str) > 50:
                    value_str = value_str[:47] + "..."
                print(f"{prefix}  Attribute: {attr_name} = {value_str}")
        except Exception as e:
            print(f"{prefix}  Error inspecting {attr_name}: {e}")

try:
    print("\n==== MCP Module Inspection ====\n")
    import mcp
    
    # Print version
    print(f"MCP Version: {getattr(mcp, '__version__', 'Unknown')}")
    print(f"MCP Path: {mcp.__file__}")
    print("")
    
    # Inspect the module structure
    inspect_module(mcp)
    
    # Check specific components
    print("\n==== Checking Specific Components ====\n")
    
    # Check for Server class
    if hasattr(mcp, 'Server'):
        print("mcp.Server: Found")
    else:
        print("mcp.Server: Not found")
    
    # Check for server submodule
    try:
        from mcp import server
        print("mcp.server module: Found")
        if hasattr(server, 'Server'):
            print("mcp.server.Server: Found")
        else:
            print("mcp.server.Server: Not found")
    except ImportError:
        print("mcp.server module: Not found")
    
    # Check for MCPServer
    try:
        from mcp.server import MCPServer
        print("mcp.server.MCPServer: Found")
    except ImportError:
        print("mcp.server.MCPServer: Not found")
    
    # Check for types
    try:
        from mcp.types import Tool, Resource
        print("mcp.types.Tool and Resource: Found")
    except ImportError:
        print("mcp.types.Tool and Resource: Not found")
        
    print("\n==== MCP Inspection Complete ====\n")

except ImportError:
    print("MCP module is not installed.")
except Exception as e:
    print(f"Error during inspection: {e}") 