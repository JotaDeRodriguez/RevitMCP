"""
Revit API Module
Provides a clean interface for working with the Revit API and RPC server functionality.
"""

import sys
import os
import json
import traceback
import time
import threading
from collections import namedtuple

# Revit API imports
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System')
clr.AddReference('System.Net')
clr.AddReference('System.Threading')
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from System.Net import HttpListener, HttpListenerContext
from System.Text import Encoding
from System.Threading import Thread, ThreadStart

# Structure to hold element data
ElementInfo = namedtuple('ElementInfo', ['id', 'name', 'category'])

class RevitAPIWrapper:
    """Wrapper for Revit API operations."""
    
    def __init__(self, doc=None, uidoc=None):
        """Initialize with optional document and UI document."""
        # If doc and uidoc are not provided, try to get from __revit__
        if doc is None or uidoc is None:
            try:
                import __main__
                self.doc = __main__.__revit__.ActiveUIDocument.Document
                self.uidoc = __main__.__revit__.ActiveUIDocument
            except Exception as e:
                raise RuntimeError("Failed to get active document. Are you running in Revit?")
        else:
            self.doc = doc
            self.uidoc = uidoc
    
    def get_elements_by_category(self, category_name):
        """Get elements by category name."""
        # Convert category name to BuiltInCategory enum name
        # Example: "Walls" -> "OST_Walls"
        built_in_cat_name = 'OST_' + category_name.replace(" ", "").replace("-", "_")
        
        try:
            # Get BuiltInCategory from name
            bic = getattr(BuiltInCategory, built_in_cat_name)
        except AttributeError:
            raise ValueError(f"Invalid or unsupported category name: '{category_name}' (tried '{built_in_cat_name}')")
        
        # Get elements from the document
        collector = FilteredElementCollector(self.doc).OfCategory(bic).WhereElementIsNotElementType()
        elements = collector.ToElements()
        
        # Convert to ElementInfo objects
        result = []
        for elem in elements:
            try:
                result.append(ElementInfo(
                    id=elem.Id.IntegerValue,
                    name=elem.Name or "<Unnamed>",
                    category=elem.Category.Name if elem.Category else category_name
                ))
            except Exception as e:
                # Add with error information if something goes wrong
                result.append(ElementInfo(
                    id=elem.Id.IntegerValue,
                    name=f"<Error: {e}>",
                    category=category_name
                ))
        
        return result
    
    def get_element_parameter(self, element_id, parameter_name):
        """Get parameter value for an element."""
        # Get element by ID
        element = self.doc.GetElement(ElementId(element_id))
        if not element:
            raise ValueError(f"Element with ID {element_id} not found")
        
        # Get parameter
        param = element.LookupParameter(parameter_name)
        if not param:
            return None
        
        # Get parameter value based on storage type
        storage_type = param.StorageType
        if storage_type == StorageType.String:
            return param.AsString()
        elif storage_type == StorageType.Integer:
            return param.AsInteger()
        elif storage_type == StorageType.Double:
            return param.AsDouble()
        elif storage_type == StorageType.ElementId:
            element_id = param.AsElementId().IntegerValue
            return None if element_id == -1 else element_id
        else:
            return f"<Unsupported StorageType: {storage_type}>"
    
    def select_elements(self, element_ids):
        """Select elements in the UI by their IDs."""
        if not element_ids:
            # Clear selection if no IDs provided
            self.uidoc.Selection.SetElementIds([])
            return 0
        
        # Create ElementId collection
        id_collection = List[ElementId]()
        for id_int in element_ids:
            id_collection.Add(ElementId(id_int))
        
        # Set selection
        self.uidoc.Selection.SetElementIds(id_collection)
        
        # Return the number of selected elements
        return len(element_ids)
    
    def get_element_by_id(self, element_id):
        """Get element by ID."""
        element = self.doc.GetElement(ElementId(element_id))
        if not element:
            return None
            
        try:
            category_name = element.Category.Name if element.Category else "<No Category>"
            return ElementInfo(
                id=element_id,
                name=element.Name or "<Unnamed>",
                category=category_name
            )
        except Exception as e:
            return ElementInfo(
                id=element_id,
                name=f"<Error: {e}>",
                category="<Error>"
            )
    
    def get_selected_elements(self):
        """Get currently selected elements."""
        selected_ids = self.uidoc.Selection.GetElementIds()
        result = []
        
        for element_id in selected_ids:
            element = self.doc.GetElement(element_id)
            if element:
                try:
                    category_name = element.Category.Name if element.Category else "<No Category>"
                    result.append(ElementInfo(
                        id=element_id.IntegerValue,
                        name=element.Name or "<Unnamed>",
                        category=category_name
                    ))
                except Exception as e:
                    result.append(ElementInfo(
                        id=element_id.IntegerValue,
                        name=f"<Error: {e}>",
                        category="<Error>"
                    ))
        
        return result 

class RpcServer:
    """
    Simple HTTP server that runs in Revit and exposes API functionality.
    """
    
    def __init__(self, port=9877, logger=None):
        self.port = port
        self.listener = None
        self.thread = None
        self.running = False
        self.api = RevitAPIWrapper()
        self.logger = logger
        
    def log(self, message, level="info"):
        """Log a message if logger is available."""
        if self.logger:
            if level == "info":
                self.logger.info(message)
            elif level == "error":
                self.logger.error(message)
            elif level == "debug":
                self.logger.debug(message)
        
    def start(self):
        """Start the RPC server."""
        if self.running:
            self.log("RPC Server already running")
            return True
            
        try:
            # Check if port is available
            self._check_port_available()
            
            # Create HTTP listener
            self.listener = HttpListener()
            self.listener.Prefixes.Add(f"http://localhost:{self.port}/")
            self.listener.Start()
            
            # Start server in a background thread
            self.thread = Thread(ThreadStart(self._serve))
            self.thread.IsBackground = True
            self.thread.Start()
            
            self.running = True
            self.log(f"Revit RPC Server started on port {self.port}")
            return True
            
        except Exception as e:
            self.log(f"Failed to start RPC Server: {e}", "error")
            if self.logger:
                self.logger.debug(traceback.format_exc())
            return False
    
    def _check_port_available(self):
        """Check if the server port is available."""
        try:
            from System.Net.Sockets import Socket, AddressFamily, SocketType, ProtocolType
            from System.Net.Sockets import SocketOptionLevel, SocketOptionName
            from System.Net import IPEndPoint, IPAddress
            
            sock = Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp)
            sock.SetSocketOption(SocketOptionLevel.Socket, SocketOptionName.ReuseAddress, True)
            
            try:
                sock.Bind(IPEndPoint(IPAddress.Parse("127.0.0.1"), self.port))
                sock.Close()
            except Exception as e:
                sock.Close()
                raise RuntimeError(f"Port {self.port} is already in use. Please choose a different port.")
                
        except Exception as e:
            raise RuntimeError(f"Error checking port availability: {e}")
    
    def stop(self):
        """Stop the RPC server."""
        if not self.running:
            self.log("RPC Server not running", "info")
            return
            
        try:
            self.running = False
            if self.listener:
                self.listener.Stop()
                self.listener.Close()
                self.listener = None
            self.log("Revit RPC Server stopped", "info")
        except Exception as e:
            self.log(f"Error stopping RPC Server: {e}", "error")
            if self.logger:
                self.logger.debug(traceback.format_exc())
    
    def _serve(self):
        """Main server loop."""
        self.log("RPC server started listening", "debug")
        
        while self.running:
            try:
                if not self.listener.IsListening:
                    self.log("Listener stopped, exiting server loop", "debug")
                    break
                    
                # Wait for a request with a timeout
                context = None
                ready = self.listener.BeginGetContext(None, None)
                if ready.AsyncWaitHandle.WaitOne(1000):  # 1 second timeout
                    context = self.listener.EndGetContext(ready)
                
                if not context:
                    continue  # No request received, check if we should still be running
                    
                # Process the request
                request = context.Request
                response = context.Response
                
                # Read request data
                request_body = ""
                if request.HasEntityBody:
                    request_stream = request.InputStream
                    reader = System.IO.StreamReader(request_stream)
                    request_body = reader.ReadToEnd()
                    reader.Close()
                    request_stream.Close()
                
                # Get the path without leading/trailing slashes
                path = request.Url.AbsolutePath.Trim('/')
                
                self.log(f"RPC Request: {request.HttpMethod} {path}", "debug")
                
                # Process request
                if path == "ping":
                    response_data = {"status": "success", "message": "Revit RPC Server is running"}
                elif path == "get_elements":
                    response_data = self._handle_get_elements(request_body)
                elif path == "get_parameter":
                    response_data = self._handle_get_parameter(request_body)
                elif path == "select_elements":
                    response_data = self._handle_select_elements(request_body)
                else:
                    response_data = {"status": "error", "message": f"Unknown endpoint: {path}"}
                
                # Send response
                response_json = json.dumps(response_data)
                buffer = Encoding.UTF8.GetBytes(response_json)
                response.ContentLength64 = buffer.Length
                response.ContentType = "application/json"
                output = response.OutputStream
                output.Write(buffer, 0, buffer.Length)
                output.Close()
                
            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    self.log(f"Error in RPC server: {e}", "error")
                    if self.logger:
                        self.logger.debug(traceback.format_exc())
                time.sleep(0.5)  # Prevent tight loop in case of repeated errors
    
    def _handle_get_elements(self, request_body):
        """Handle request to get elements by category."""
        try:
            data = json.loads(request_body) if request_body else {}
            category = data.get('category')
            
            if not category:
                return {"status": "error", "message": "Missing 'category' in request"}
                
            elements = self.api.get_elements_by_category(category)
            
            # Convert to serializable format
            result = []
            for elem in elements:
                result.append({
                    "id": elem.id,
                    "name": elem.name,
                    "category": elem.category
                })
                
            return {"status": "success", "data": result}
            
        except Exception as e:
            self.log(f"Error getting elements: {e}", "error")
            return {"status": "error", "message": str(e)}
    
    def _handle_get_parameter(self, request_body):
        """Handle request to get parameter value."""
        try:
            data = json.loads(request_body) if request_body else {}
            element_id = data.get('element_id')
            parameter_name = data.get('parameter_name')
            
            if element_id is None or parameter_name is None:
                return {"status": "error", "message": "Missing 'element_id' or 'parameter_name' in request"}
                
            value = self.api.get_element_parameter(element_id, parameter_name)
            return {"status": "success", "data": value}
            
        except Exception as e:
            self.log(f"Error getting parameter: {e}", "error")
            return {"status": "error", "message": str(e)}
    
    def _handle_select_elements(self, request_body):
        """Handle request to select elements."""
        try:
            data = json.loads(request_body) if request_body else {}
            element_ids = data.get('element_ids', [])
            
            count = self.api.select_elements(element_ids)
            return {"status": "success", "data": count}
            
        except Exception as e:
            self.log(f"Error selecting elements: {e}", "error")
            return {"status": "error", "message": str(e)} 