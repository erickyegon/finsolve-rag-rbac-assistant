"""
Document MCP Server for FinSolve RBAC Chatbot
Implements MCP server for document management and retrieval with role-based permissions.

Author: Dr. Erick K. Yegon
Version: 1.0.0
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from mcp.server import FastMCP
from mcp.types import Tool, TextContent, Resource
from loguru import logger

from ...core.config import UserRole, ROLE_PERMISSIONS
from ...utils.document_manager import document_manager


class DocumentMCPServer:
    """MCP Server for Document operations"""
    
    def __init__(self, data_directory: str = "data"):
        self.server = FastMCP("document-server")
        self.data_directory = Path(data_directory)
        
        # Register tools
        self._register_tools()
        
        logger.info("Document MCP Server initialized")
    
    def _register_tools(self):
        """Register MCP tools for Document operations"""
        
        @self.server.tool()
        async def search_documents(user_role: str, query: str, department: Optional[str] = None, 
                                 document_type: Optional[str] = None) -> str:
            """Search documents with role-based access control"""
            try:
                # Check permissions
                if not self._check_permission(user_role, "document_search"):
                    return json.dumps({
                        "error": "Access denied: Insufficient permissions for document search",
                        "required_role": "Any authenticated user"
                    })
                
                # Apply department filter based on user role
                user_dept = self._get_user_department(user_role)
                if user_role.upper() not in ['C_LEVEL'] and department and department != user_dept:
                    return json.dumps({
                        "error": f"Access denied: Cannot search documents in {department} department",
                        "allowed_department": user_dept
                    })
                
                # Perform document search using document manager
                search_results = document_manager.search_documents(
                    query=query,
                    department=department or user_dept,
                    document_type=document_type
                )
                
                return json.dumps({
                    "query": query,
                    "department": department or user_dept,
                    "document_type": document_type,
                    "results": search_results,
                    "access_level": user_role,
                    "search_timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error in search_documents: {str(e)}")
                return json.dumps({"error": f"Failed to search documents: {str(e)}"})
        
        @self.server.tool()
        async def get_document_content(user_role: str, document_id: str) -> str:
            """Get document content with role-based access control"""
            try:
                # Check permissions
                if not self._check_permission(user_role, "document_read"):
                    return json.dumps({
                        "error": "Access denied: Insufficient permissions to read documents",
                        "required_role": "Any authenticated user"
                    })
                
                # Get document metadata first
                doc_metadata = document_manager.get_document_metadata(document_id)
                if not doc_metadata:
                    return json.dumps({
                        "error": f"Document {document_id} not found"
                    })
                
                # Check department access
                doc_department = doc_metadata.get('department')
                user_dept = self._get_user_department(user_role)
                
                if user_role.upper() not in ['C_LEVEL'] and doc_department != user_dept:
                    return json.dumps({
                        "error": f"Access denied: Document belongs to {doc_department} department",
                        "user_department": user_dept
                    })
                
                # Get document content
                content = document_manager.get_document_content(document_id)
                
                return json.dumps({
                    "document_id": document_id,
                    "metadata": doc_metadata,
                    "content": content,
                    "access_level": user_role,
                    "retrieved_at": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error in get_document_content: {str(e)}")
                return json.dumps({"error": f"Failed to retrieve document content: {str(e)}"})
        
        @self.server.tool()
        async def list_documents(user_role: str, department: Optional[str] = None, 
                               document_type: Optional[str] = None) -> str:
            """List documents with role-based filtering"""
            try:
                # Check permissions
                if not self._check_permission(user_role, "document_list"):
                    return json.dumps({
                        "error": "Access denied: Insufficient permissions to list documents",
                        "required_role": "Any authenticated user"
                    })
                
                # Apply department filter based on user role
                user_dept = self._get_user_department(user_role)
                if user_role.upper() not in ['C_LEVEL']:
                    # Non-C_LEVEL users can only see their department's documents
                    department = user_dept
                
                # Get document list
                documents = document_manager.list_documents(
                    department=department,
                    document_type=document_type
                )
                
                # Filter sensitive information based on role
                filtered_docs = []
                for doc in documents:
                    filtered_doc = self._filter_document_metadata(doc, user_role)
                    filtered_docs.append(filtered_doc)
                
                return json.dumps({
                    "department": department,
                    "document_type": document_type,
                    "document_count": len(filtered_docs),
                    "documents": filtered_docs,
                    "access_level": user_role,
                    "retrieved_at": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error in list_documents: {str(e)}")
                return json.dumps({"error": f"Failed to list documents: {str(e)}"})
        
        @self.server.tool()
        async def get_document_summary(user_role: str, document_id: str) -> str:
            """Get document summary with role-based access control"""
            try:
                # Check permissions
                if not self._check_permission(user_role, "document_read"):
                    return json.dumps({
                        "error": "Access denied: Insufficient permissions to read documents",
                        "required_role": "Any authenticated user"
                    })
                
                # Get document metadata
                doc_metadata = document_manager.get_document_metadata(document_id)
                if not doc_metadata:
                    return json.dumps({
                        "error": f"Document {document_id} not found"
                    })
                
                # Check department access
                doc_department = doc_metadata.get('department')
                user_dept = self._get_user_department(user_role)
                
                if user_role.upper() not in ['C_LEVEL'] and doc_department != user_dept:
                    return json.dumps({
                        "error": f"Access denied: Document belongs to {doc_department} department",
                        "user_department": user_dept
                    })
                
                # Generate document summary
                summary = document_manager.generate_document_summary(document_id)
                
                return json.dumps({
                    "document_id": document_id,
                    "metadata": doc_metadata,
                    "summary": summary,
                    "access_level": user_role,
                    "generated_at": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error in get_document_summary: {str(e)}")
                return json.dumps({"error": f"Failed to generate document summary: {str(e)}"})
    
    def _check_permission(self, user_role: str, operation: str) -> bool:
        """Check if user role has permission for specific operation"""
        try:
            role = UserRole(user_role.upper())
            permissions = ROLE_PERMISSIONS.get(role, [])
            
            # Define permission mappings
            permission_map = {
                "document_search": ["document_access", "all_data"],
                "document_read": ["document_access", "all_data"],
                "document_list": ["document_access", "all_data"]
            }
            
            required_perms = permission_map.get(operation, [])
            return any(perm in permissions for perm in required_perms) or len(permissions) > 0
            
        except (ValueError, AttributeError):
            return False
    
    def _get_user_department(self, user_role: str) -> str:
        """Get user department based on role"""
        role_department_map = {
            "HR": "HR",
            "FINANCE": "Finance", 
            "MARKETING": "Marketing",
            "ENGINEERING": "Engineering",
            "C_LEVEL": "All",  # C_LEVEL can access all departments
            "EMPLOYEE": "General"
        }
        
        return role_department_map.get(user_role.upper(), "General")
    
    def _filter_document_metadata(self, doc_metadata: Dict[str, Any], user_role: str) -> Dict[str, Any]:
        """Filter document metadata based on user role"""
        try:
            # Base fields available to all users
            base_fields = ['document_id', 'filename', 'department', 'document_type', 'size', 'modified']
            
            # Additional fields for authorized roles
            if user_role.upper() in ['HR', 'FINANCE', 'MARKETING', 'ENGINEERING', 'C_LEVEL']:
                additional_fields = ['upload_date', 'uploaded_by', 'content_length', 'tags']
                allowed_fields = base_fields + additional_fields
            else:
                allowed_fields = base_fields
            
            # Filter metadata
            filtered_metadata = {k: v for k, v in doc_metadata.items() if k in allowed_fields}
            
            return filtered_metadata
            
        except Exception as e:
            logger.error(f"Error filtering document metadata: {str(e)}")
            return {"error": "Failed to filter document metadata"}
    
    async def start(self):
        """Start the MCP server"""
        try:
            await self.server.run()
            logger.info("Document MCP Server started successfully")
        except Exception as e:
            logger.error(f"Failed to start Document MCP Server: {str(e)}")
            raise
    
    def get_tools(self) -> List[Tool]:
        """Get list of available tools"""
        return [
            Tool(
                name="search_documents",
                description="Search documents with role-based access control",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_role": {"type": "string", "description": "User role"},
                        "query": {"type": "string", "description": "Search query"},
                        "department": {"type": "string", "description": "Optional department filter"},
                        "document_type": {"type": "string", "description": "Optional document type filter"}
                    },
                    "required": ["user_role", "query"]
                }
            ),
            Tool(
                name="get_document_content",
                description="Get document content with role-based access control",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_role": {"type": "string", "description": "User role"},
                        "document_id": {"type": "string", "description": "Document ID"}
                    },
                    "required": ["user_role", "document_id"]
                }
            ),
            Tool(
                name="list_documents",
                description="List documents with role-based filtering",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_role": {"type": "string", "description": "User role"},
                        "department": {"type": "string", "description": "Optional department filter"},
                        "document_type": {"type": "string", "description": "Optional document type filter"}
                    },
                    "required": ["user_role"]
                }
            ),
            Tool(
                name="get_document_summary",
                description="Get document summary with role-based access control",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_role": {"type": "string", "description": "User role"},
                        "document_id": {"type": "string", "description": "Document ID"}
                    },
                    "required": ["user_role", "document_id"]
                }
            )
        ]


# Create global instance
document_mcp_server = DocumentMCPServer()
