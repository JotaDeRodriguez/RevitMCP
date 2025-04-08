"""
RevitMCP Server - MCP Implementation
Modern implementation of MCP server for Revit integration using the official MCP package.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional, AsyncIterator
from contextlib import asynccontextmanager
import asyncio
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "server_log.txt")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RevitMCP")

# Try to import MCP and required libraries
try:
    # Import MCP and required dependencies
    from mcp.server.fastmcp import FastMCP, Context, Image
    import httpx
except ImportError as e:
    logger.error(f"Failed to import MCP: {e}")
    logger.error("Please install the MCP package: pip install mcp[cli]")
    sys.exit(1)

# Try to import Anthropic SDK for Claude integration
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    logger.warning("Anthropic SDK not available. Claude integration will be limited.")
    ANTHROPIC_AVAILABLE = False

# Current configuration
CONFIG = {
    "revit_port": 9877,
    "mcp_port": 9876,
    "model": "claude-3-7-sonnet-latest",
    "api_key": None
}

# Context class for server lifespan management
class RevitContext:
    """Context for the RevitMCP server."""
    
    def __init__(self, client: httpx.AsyncClient, api_key: Optional[str] = None):
        self.client = client
        self.api_key = api_key
        self.base_url = f"http://localhost:{CONFIG['revit_port']}"
        
    async def call_revit(self, endpoint: str, data: Dict[str, Any] = None) -> Any:
        """
        Call the Revit RPC server.
        
        Args:
            endpoint: The API endpoint to call
            data: The JSON payload to send
            
        Returns:
            The data returned from the Revit RPC server
        """
        try:
            # Make a POST request to the Revit RPC server
            response = await self.client.post(
                f"{self.base_url}/{endpoint}",
                json=data or {},
                timeout=30.0
            )
            
            # Check if the response was successful
            response.raise_for_status()
            
            # Parse and validate the response
            response_data = response.json()
            
            if response_data.get("status") == "error":
                logger.error(f"Revit RPC error: {response_data.get('message', 'Unknown error')}")
                raise Exception(f"Revit RPC error: {response_data.get('message', 'Unknown error')}")
                
            return response_data.get("data")
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling Revit RPC ({endpoint}): {e}")
            raise Exception(f"HTTP error communicating with Revit: {e}")
            
        except Exception as e:
            logger.error(f"Error calling Revit RPC ({endpoint}): {e}")
            logger.error(traceback.format_exc())
            raise Exception(f"Error communicating with Revit: {str(e)}")
            
    async def ping(self) -> bool:
        """Check if the Revit RPC server is available."""
        try:
            response = await self.client.get(f"{self.base_url}/ping", timeout=5.0)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.debug(f"Ping failed: {e}")
            return False


# FastMCP server with lifespan management
@asynccontextmanager
async def revit_lifespan(server: FastMCP) -> AsyncIterator[RevitContext]:
    """Manage the RevitMCP server lifespan."""
    # Initialize the HTTP client with retry logic
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    timeout = httpx.Timeout(30.0, connect=5.0)
    transport = httpx.AsyncHTTPTransport(retries=3)
    
    client = httpx.AsyncClient(
        limits=limits,
        timeout=timeout,
        transport=transport
    )
    
    try:
        # Create the context and verify Revit connection
        ctx = RevitContext(client, CONFIG.get("api_key"))
        
        # Try to ping Revit
        is_connected = await ctx.ping()
        if is_connected:
            logger.info("Successfully connected to Revit RPC server")
        else:
            logger.warning("Could not connect to Revit RPC server. Some features may not work.")
        
        # Yield the context to the server
        yield ctx
        
    finally:
        # Clean up resources
        await client.aclose()


# Create the MCP server
mcp = FastMCP(
    "RevitMCP", 
    description="MCP Server for Revit integration",
    lifespan=revit_lifespan,
    dependencies=["mcp", "httpx", "anthropic"]
)


# Resource for getting Revit categories
@mcp.resource("revit://categories")
async def get_categories(ctx: Context) -> List[str]:
    """Get all available categories in the current Revit document."""
    logger.info("Resource request: get_categories")
    
    revit_ctx = ctx.request_context.lifespan_context
    return await revit_ctx.call_revit("get_categories", {})


# Resource for getting elements by category
@mcp.resource("revit://elements/{category}")
async def get_elements(category: str, ctx: Context) -> List[Dict[str, Any]]:
    """Get elements of a specified category from the Revit model."""
    logger.info(f"Resource request: get_elements for category '{category}'")
    
    revit_ctx = ctx.request_context.lifespan_context
    return await revit_ctx.call_revit("get_elements", {"category": category})


# Tool for getting parameter value
@mcp.tool()
async def get_element_parameter(element_id: int, parameter_name: str, ctx: Context) -> Optional[str]:
    """
    Get a parameter value for a specific element.
    
    Args:
        element_id: The element ID
        parameter_name: The parameter name to retrieve
        
    Returns:
        The parameter value as a string, or None if the parameter doesn't exist
    """
    logger.info(f"Tool request: get_element_parameter for element {element_id}, parameter '{parameter_name}'")
    
    revit_ctx = ctx.request_context.lifespan_context
    result = await revit_ctx.call_revit("get_parameter", {
        "element_id": element_id,
        "parameter_name": parameter_name
    })
    
    return str(result) if result is not None else None


# Tool for selecting elements
@mcp.tool()
async def select_elements(element_ids: List[int], ctx: Context) -> int:
    """
    Select elements in Revit by their IDs.
    
    Args:
        element_ids: List of element IDs to select
        
    Returns:
        The number of elements successfully selected
    """
    logger.info(f"Tool request: select_elements for {len(element_ids)} elements")
    
    revit_ctx = ctx.request_context.lifespan_context
    result = await revit_ctx.call_revit("select_elements", {
        "element_ids": element_ids
    })
    
    return int(result)


# Tool for creating a wall
@mcp.tool()
async def create_wall(
    start_point: Dict[str, float],
    end_point: Dict[str, float],
    height: float,
    ctx: Context,
    width: float = 200.0,
    level_id: Optional[int] = None,
    wall_type_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a wall in Revit.
    
    Args:
        start_point: Start point coordinates {x, y, z} in millimeters
        end_point: End point coordinates {x, y, z} in millimeters
        height: Height of the wall in millimeters
        width: Width/thickness of the wall in millimeters (default: 200.0)
        level_id: Level ID (optional)
        wall_type_id: Wall type ID (optional)
        
    Returns:
        Information about the created wall including its ID
    """
    logger.info(f"Tool request: create_wall")
    
    data = {
        "start_point": start_point,
        "end_point": end_point,
        "height": height,
        "width": width
    }
    
    if level_id is not None:
        data["level_id"] = level_id
        
    if wall_type_id is not None:
        data["wall_type_id"] = wall_type_id
    
    revit_ctx = ctx.request_context.lifespan_context
    return await revit_ctx.call_revit("create_wall", data)


# Tool for creating a line-based element
@mcp.tool()
async def create_line_based_element(
    name: str,
    location_line: Dict[str, Dict[str, float]],
    thickness: float,
    height: float,
    ctx: Context,
    type_id: Optional[int] = None,
    base_level: Optional[int] = None,
    base_offset: float = 0.0
) -> Dict[str, Any]:
    """
    Create a line-based element in Revit such as walls, beams, or pipes.
    
    Args:
        name: Description of the element (e.g., wall, beam)
        location_line: The line defining the element's location {p0: {x, y, z}, p1: {x, y, z}}
        thickness: Thickness/width of the element in millimeters
        height: Height of the element in millimeters
        type_id: The ID of the family type to create (optional)
        base_level: Base level ID (optional)
        base_offset: Offset from the base level in millimeters (default: 0.0)
        
    Returns:
        Information about the created element including its ID
    """
    logger.info(f"Tool request: create_line_based_element for {name}")
    
    data = {
        "name": name,
        "location_line": location_line,
        "thickness": thickness,
        "height": height,
        "base_offset": base_offset
    }
    
    if type_id is not None:
        data["type_id"] = type_id
        
    if base_level is not None:
        data["base_level"] = base_level
    
    revit_ctx = ctx.request_context.lifespan_context
    return await revit_ctx.call_revit("create_line_based_element", data)


# Main function to run the server
async def run_server(mcp_port: int, revit_port: int, model: str, api_key: Optional[str] = None):
    """Run the MCP server."""
    # Update configuration
    CONFIG["revit_port"] = revit_port
    CONFIG["mcp_port"] = mcp_port
    CONFIG["model"] = model
    CONFIG["api_key"] = api_key
    
    logger.info(f"Starting RevitMCP server (MCP implementation) on port {mcp_port}")
    logger.info(f"Connecting to Revit RPC server on port {revit_port}")
    
    # Run the MCP server
    await mcp.run_async_app(
        host="127.0.0.1",
        port=mcp_port
    )


# Entry point when run directly
def main():
    """Main entry point for the server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="RevitMCP Server (MCP Implementation)")
    parser.add_argument("--mcp-port", type=int, default=9876, help="Port for the MCP server")
    parser.add_argument("--revit-port", type=int, default=9877, help="Port for the Revit RPC server")
    parser.add_argument("--model", type=str, default="claude-3-7-sonnet-latest", help="Model for Claude")
    parser.add_argument("--api-key", type=str, help="API key for Claude")
    args = parser.parse_args()
    
    try:
        # Run the server
        asyncio.run(run_server(args.mcp_port, args.revit_port, args.model, args.api_key))
        return 0
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main()) 