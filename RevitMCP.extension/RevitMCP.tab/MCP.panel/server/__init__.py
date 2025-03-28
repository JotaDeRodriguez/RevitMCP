"""Revit MCP Server package.

This directory contains the server modules for the Revit MCP integration.
- revit_api_server.py: HTTP server that provides Revit API access
- dummy_server.py: Simple server for testing the MCP integration
"""

# Import server modules to make them available to other modules
try:
    from .revit_api_server import RevitAPIServer
except ImportError:
    # The module may not be available during initialization, but that's okay
    pass

try:
    from .dummy_server import DummyMCPServer
except ImportError:
    # The module may not be available during initialization, but that's okay
    pass 