"""Revit API HTTP server for exposing Revit functionality."""

import os
import sys
import threading
import socket
import json
import traceback

try:
    # For logging
    from pyrevit import script
    logger = script.get_logger()
except:
    import logging
    logger = logging.getLogger(__name__)

class RevitAPIServer:
    """Simple HTTP server that exposes Revit API functionality."""
    
    def __init__(self, port=9877):
        """Initialize the server with specified port."""
        self.port = port
        self.running = False
        self.server_thread = None
        
    def start(self):
        """Start the server in a separate thread."""
        if self.running:
            logger.info("RevitAPI server is already running")
            return
            
        self.running = True
        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        logger.info("RevitAPI server started on port {}".format(self.port))
        
    def stop(self):
        """Stop the server."""
        self.running = False
        logger.info("RevitAPI server stopped")
        
    def _run_server(self):
        """Run the HTTP server."""
        try:
            # Import Revit API
            from pyrevit import revit, DB
            
            # Create socket
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('localhost', self.port))
            server_socket.listen(1)
            server_socket.settimeout(1)  # 1 second timeout for clean shutdown
            
            logger.info("RevitAPI server running on port {}".format(self.port))
            
            # Main server loop
            while self.running:
                try:
                    client_socket, address = server_socket.accept()
                    self._handle_request(client_socket, revit, DB)
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error("Error in server loop: {}".format(e))
                    
        except Exception as e:
            logger.error("Error starting RevitAPI server: {}".format(e))
            self.running = False
        finally:
            if 'server_socket' in locals():
                server_socket.close()
    
    def _handle_request(self, client_socket, revit, DB):
        """Handle an HTTP request."""
        try:
            # Receive data
            data = ""
            while True:
                chunk = client_socket.recv(4096).decode('utf-8')
                data += chunk
                if len(chunk) < 4096:
                    break
            
            # Parse HTTP headers
            headers = data.split('\r\n\r\n')[0]
            request_line = headers.split('\r\n')[0]
            method, path, _ = request_line.split(' ')
            
            # Get request body for POST requests
            body = ""
            if method == 'POST' and len(data.split('\r\n\r\n')) > 1:
                body = data.split('\r\n\r\n')[1]
            
            # Handle endpoints
            if path == '/api/model/info' and method == 'GET':
                self._handle_model_info(client_socket, revit, DB)
            elif path == '/api/elements' and method == 'GET':
                self._handle_elements(client_socket, revit, DB)
            elif path == '/api/query' and method == 'POST':
                self._handle_query(client_socket, revit, DB, body)
            else:
                # Handle 404
                response = 'HTTP/1.1 404 Not Found\r\n\r\n'
                client_socket.sendall(response.encode('utf-8'))
        except Exception as e:
            logger.error("Error handling request: {}".format(e))
            # Send error response
            response = 'HTTP/1.1 500 Internal Server Error\r\nContent-Type: application/json\r\n\r\n'
            response += json.dumps({"error": str(e)})
            try:
                client_socket.sendall(response.encode('utf-8'))
            except:
                pass
        finally:
            client_socket.close()
    
    def _handle_model_info(self, client_socket, revit, DB):
        """Handle model info request."""
        try:
            doc = revit.doc
            if not doc:
                response_data = {"error": "No active document"}
            else:
                project_info = doc.ProjectInformation
                response_data = {
                    "title": doc.Title,
                    "path": doc.PathName,
                    "project_number": project_info.Number if project_info else "",
                    "project_name": project_info.Name if project_info else "",
                    "element_count": doc.GetElementCount()
                }
            
            # Send response
            response = 'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n'
            response += json.dumps(response_data)
            client_socket.sendall(response.encode('utf-8'))
        except Exception as e:
            logger.error("Error handling model info: {}".format(e))
            response = 'HTTP/1.1 500 Internal Server Error\r\nContent-Type: application/json\r\n\r\n'
            response += json.dumps({"error": str(e)})
            client_socket.sendall(response.encode('utf-8'))
    
    def _handle_elements(self, client_socket, revit, DB):
        """Handle elements request."""
        try:
            doc = revit.doc
            if not doc:
                response_data = {"error": "No active document"}
            else:
                # Get all elements
                elements = DB.FilteredElementCollector(doc).WhereElementIsNotElementType().ToElements()
                
                # Convert to list of dicts
                element_list = []
                for element in elements[:100]:  # Limit to 100 for performance
                    try:
                        element_dict = {
                            "id": element.Id.IntegerValue,
                            "name": getattr(element, 'Name', ''),
                            "category": element.Category.Name if element.Category else "No Category"
                        }
                        element_list.append(element_dict)
                    except:
                        pass
                
                response_data = {
                    "count": len(elements),
                    "elements": element_list
                }
            
            # Send response
            response = 'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n'
            response += json.dumps(response_data)
            client_socket.sendall(response.encode('utf-8'))
        except Exception as e:
            logger.error("Error handling elements: {}".format(e))
            response = 'HTTP/1.1 500 Internal Server Error\r\nContent-Type: application/json\r\n\r\n'
            response += json.dumps({"error": str(e)})
            client_socket.sendall(response.encode('utf-8'))
    
    def _handle_query(self, client_socket, revit, DB, body):
        """Handle custom query request."""
        try:
            query = json.loads(body)
            query_type = query.get("type", "")
            
            doc = revit.doc
            if not doc:
                response_data = {"error": "No active document"}
            else:
                # Simple query dispatcher
                if query_type == "walls":
                    response_data = self._query_walls(doc, DB, query)
                elif query_type == "doors":
                    response_data = self._query_doors(doc, DB, query)
                elif query_type == "rooms":
                    response_data = self._query_rooms(doc, DB, query)
                else:
                    response_data = {"error": "Unknown query type: {}".format(query_type)}
            
            # Send response
            response = 'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n'
            response += json.dumps(response_data)
            client_socket.sendall(response.encode('utf-8'))
        except Exception as e:
            logger.error("Error handling query: {}".format(e))
            response = 'HTTP/1.1 500 Internal Server Error\r\nContent-Type: application/json\r\n\r\n'
            response += json.dumps({"error": str(e)})
            client_socket.sendall(response.encode('utf-8'))
    
    def _query_walls(self, doc, DB, query):
        """Query walls in the document."""
        filter = DB.ElementCategoryFilter(DB.BuiltInCategory.OST_Walls)
        walls = DB.FilteredElementCollector(doc).WherePasses(filter).WhereElementIsNotElementType().ToElements()
        
        wall_list = []
        for wall in walls:
            try:
                wall_dict = {
                    "id": wall.Id.IntegerValue,
                    "name": wall.Name,
                    "length": wall.Location.Curve.Length if hasattr(wall.Location, 'Curve') else 0,
                    "type": doc.GetElement(wall.GetTypeId()).Name if wall.GetTypeId() else "Unknown Type"
                }
                wall_list.append(wall_dict)
            except:
                pass
                
        return {
            "count": len(walls),
            "walls": wall_list
        }
    
    def _query_doors(self, doc, DB, query):
        """Query doors in the document."""
        filter = DB.ElementCategoryFilter(DB.BuiltInCategory.OST_Doors)
        doors = DB.FilteredElementCollector(doc).WherePasses(filter).WhereElementIsNotElementType().ToElements()
        
        door_list = []
        for door in doors:
            try:
                door_dict = {
                    "id": door.Id.IntegerValue,
                    "name": door.Name,
                    "type": doc.GetElement(door.GetTypeId()).Name if door.GetTypeId() else "Unknown Type"
                }
                door_list.append(door_dict)
            except:
                pass
                
        return {
            "count": len(doors),
            "doors": door_list
        }
    
    def _query_rooms(self, doc, DB, query):
        """Query rooms in the document."""
        filter = DB.ElementCategoryFilter(DB.BuiltInCategory.OST_Rooms)
        rooms = DB.FilteredElementCollector(doc).WherePasses(filter).WhereElementIsNotElementType().ToElements()
        
        room_list = []
        for room in rooms:
            try:
                room_dict = {
                    "id": room.Id.IntegerValue,
                    "name": room.Name,
                    "number": room.Number,
                    "area": room.Area
                }
                room_list.append(room_dict)
            except:
                pass
                
        return {
            "count": len(rooms),
            "rooms": room_list
        } 