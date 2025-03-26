from mcp.server.fastmcp import FastMCP, Context
import asyncio
import json
import socket
import logging
import os
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("revit_mcp")

# Initialize MCP server
mcp = FastMCP("Revit MCP")

# Configuration
REVIT_API_PORT = 9877  # Port for communication with Revit/PyRevit

# Revit API communication helper
async def call_revit_api(command, params=None):
    """Call the Revit API through our socket interface"""
    params = params or {}
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client.connect(('localhost', REVIT_API_PORT))
        request = {
            'command': command,
            'params': params
        }
        client.sendall(json.dumps(request).encode('utf-8'))
        
        # Get response
        response = client.recv(4096).decode('utf-8')
        return json.loads(response)
    except Exception as e:
        logger.error(f"Error calling Revit API: {str(e)}")
        return {'error': str(e)}
    finally:
        client.close()

# ======================
# MCP Tools
# ======================

@mcp.tool()
async def get_revit_info() -> dict:
    """Get basic information about the current Revit model"""
    return await call_revit_api("get_model_info")

@mcp.tool()
async def find_elements(category: str, filter_params: dict = None) -> list:
    """Find elements in the Revit model by category with optional filters"""
    return await call_revit_api("find_elements", {
        "category": category,
        "filter_params": filter_params or {}
    })

@mcp.tool()
async def get_element_parameters(element_id: str) -> dict:
    """Get all parameters for a specific element"""
    return await call_revit_api("get_element_parameters", {
        "element_id": element_id
    })

@mcp.tool()
async def set_element_parameter(element_id: str, parameter_name: str, value: str) -> bool:
    """Set a parameter value for an element"""
    result = await call_revit_api("set_element_parameter", {
        "element_id": element_id,
        "parameter_name": parameter_name,
        "value": value
    })
    return result.get("success", False)

@mcp.tool()
async def get_views() -> list:
    """Get all views in the current document"""
    return await call_revit_api("get_views")

@mcp.tool()
async def create_wall(start_point: dict, end_point: dict, height: float, wall_type_name: str = None) -> dict:
    """Create a wall between two points"""
    return await call_revit_api("create_wall", {
        "start_point": start_point,
        "end_point": end_point,
        "height": height,
        "wall_type_name": wall_type_name
    })

@mcp.tool()
async def start_transaction(name: str) -> str:
    """Start a new transaction for batch changes"""
    result = await call_revit_api("start_transaction", {
        "name": name
    })
    return result.get("transaction_id", "")

@mcp.tool()
async def commit_transaction(transaction_id: str) -> bool:
    """Commit changes in a transaction"""
    result = await call_revit_api("commit_transaction", {
        "transaction_id": transaction_id
    })
    return result.get("success", False)

# ======================
# MCP Resources
# ======================

@mcp.resource("revit://model/info")
async def get_model_info() -> dict:
    """Get information about the current Revit model"""
    return await call_revit_api("get_model_info")

@mcp.resource("revit://elements/{category}")
async def get_elements_by_category(category: str) -> list:
    """Get elements of a specific category"""
    return await call_revit_api("find_elements", {"category": category})

# ======================
# MCP Prompts
# ======================

@mcp.prompt()
def get_wall_types() -> str:
    return "Please list all wall types in the current Revit model."

@mcp.prompt()
def analyze_model() -> str:
    return "Please analyze the current Revit model and provide a summary of all elements by category."

@mcp.prompt()
def create_room_layout() -> str:
    return """Please help me create a basic room layout. I'll provide the dimensions and requirements, 
    and you can help me create the walls, doors, and windows."""

if __name__ == "__main__":
    logger.info("Starting Revit MCP Server...")
    try:
        mcp.run()
    except Exception as e:
        logger.error(f"Error running MCP server: {str(e)}")
        sys.exit(1) 