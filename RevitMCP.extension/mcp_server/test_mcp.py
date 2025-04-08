"""
Test MCP Installation

This script tests if MCP is properly installed and configured.
"""

import os
import sys
import logging
import traceback

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("MCP_Test")

def test_mcp_installation():
    """Test if MCP is installed and accessible."""
    try:
        import mcp
        logger.info(f"MCP is installed (version: {getattr(mcp, '__version__', 'unknown')})")
        logger.info(f"MCP path: {mcp.__file__}")
        
        # Check attributes
        attributes = dir(mcp)
        public_attrs = [attr for attr in attributes if not attr.startswith('_')]
        logger.info(f"Available public attributes: {public_attrs}")
        
        # Check for critical components
        if hasattr(mcp, 'Server'):
            logger.info("mcp.Server is available")
            server_class = mcp.Server
            
            # Check for server methods
            server_methods = [method for method in dir(server_class) if not method.startswith('_')]
            logger.info(f"Server methods: {server_methods}")
        else:
            logger.warning("mcp.Server is not available")
        
        # Check for server module
        if hasattr(mcp, 'server'):
            logger.info("mcp.server module is available")
            server_module = mcp.server
            
            # Check for server classes
            server_attrs = [attr for attr in dir(server_module) if not attr.startswith('_')]
            logger.info(f"Server module attributes: {server_attrs}")
            
            if hasattr(server_module, 'Server'):
                logger.info("mcp.server.Server is available")
            elif hasattr(server_module, 'MCPServer'):
                logger.info("mcp.server.MCPServer is available")
        else:
            logger.warning("mcp.server module is not available")
        
        # Check for types module
        if hasattr(mcp, 'types'):
            logger.info("mcp.types module is available")
            types_module = mcp.types
            types_attrs = [attr for attr in dir(types_module) if not attr.startswith('_')]
            logger.info(f"Types module attributes: {types_attrs}")
            
            if hasattr(types_module, 'Tool'):
                logger.info("mcp.types.Tool is available")
            
            if hasattr(types_module, 'Resource'):
                logger.info("mcp.types.Resource is available")
        else:
            logger.warning("mcp.types module is not available")
        
        # Try to create a server instance
        logger.info("Attempting to create a server instance...")
        try:
            if hasattr(mcp, 'Server'):
                server = mcp.Server("Test Server")
                logger.info("Successfully created server using mcp.Server")
            elif hasattr(mcp.server, 'Server'):
                server = mcp.server.Server("Test Server")
                logger.info("Successfully created server using mcp.server.Server")
            elif hasattr(mcp.server, 'MCPServer'):
                server = mcp.server.MCPServer("Test Server")
                logger.info("Successfully created server using mcp.server.MCPServer")
            else:
                logger.warning("Could not find a suitable Server class")
        except Exception as e:
            logger.error(f"Error creating server instance: {e}")
            logger.error(traceback.format_exc())
        
        logger.info("MCP test completed successfully")
        return True
    except ImportError:
        logger.error("MCP is not installed")
        return False
    except Exception as e:
        logger.error(f"Error testing MCP: {e}")
        logger.error(traceback.format_exc())
        return False

def test_anthropic():
    """Test if Anthropic SDK is installed and accessible."""
    try:
        import anthropic
        logger.info(f"Anthropic SDK is installed (version: {getattr(anthropic, '__version__', 'unknown')})")
        logger.info(f"Anthropic SDK path: {anthropic.__file__}")
        
        # Check client class
        if hasattr(anthropic, 'Anthropic'):
            logger.info("anthropic.Anthropic client is available")
        else:
            logger.warning("anthropic.Anthropic client is not available")
        
        logger.info("Anthropic SDK test completed successfully")
        return True
    except ImportError:
        logger.error("Anthropic SDK is not installed")
        return False
    except Exception as e:
        logger.error(f"Error testing Anthropic SDK: {e}")
        logger.error(traceback.format_exc())
        return False

def test_fastapi():
    """Test if FastAPI is installed and accessible."""
    try:
        import fastapi
        import uvicorn
        
        logger.info(f"FastAPI is installed (version: {fastapi.__version__})")
        logger.info(f"FastAPI path: {fastapi.__file__}")
        
        logger.info(f"Uvicorn is installed (version: {uvicorn.__version__})")
        logger.info(f"Uvicorn path: {uvicorn.__file__}")
        
        logger.info("FastAPI test completed successfully")
        return True
    except ImportError:
        logger.error("FastAPI or Uvicorn is not installed")
        return False
    except Exception as e:
        logger.error(f"Error testing FastAPI: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("===== MCP Installation Test =====")
    
    mcp_ok = test_mcp_installation()
    anthropic_ok = test_anthropic()
    fastapi_ok = test_fastapi()
    
    logger.info("\n===== Test Summary =====")
    logger.info(f"MCP: {'✓ Available' if mcp_ok else '✗ Not available'}")
    logger.info(f"Anthropic SDK: {'✓ Available' if anthropic_ok else '✗ Not available'}")
    logger.info(f"FastAPI/Uvicorn: {'✓ Available' if fastapi_ok else '✗ Not available'}")
    
    if mcp_ok and anthropic_ok and fastapi_ok:
        logger.info("All dependencies are installed and available.")
        sys.exit(0)
    else:
        logger.error("One or more dependencies are missing or not properly configured.")
        sys.exit(1) 