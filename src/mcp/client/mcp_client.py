"""
MCP Client for FinSolve RBAC Chatbot
Coordinates multiple MCP servers and provides unified interface.

Author: Dr. Erick K. Yegon
Version: 1.0.0
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# Note: Using direct FastMCP server calls instead of MCP client
# from mcp.client import Client  # Not available in current MCP version
# from mcp.types import Tool, CallToolRequest, CallToolResult
from loguru import logger

from ..servers.hr_server import hr_mcp_server
from ..servers.finance_server import finance_mcp_server
from ..servers.document_server import document_mcp_server


class MCPClient:
    """Unified MCP Client for coordinating multiple MCP servers"""
    
    def __init__(self):
        self.servers = {
            "hr": hr_mcp_server,
            "finance": finance_mcp_server,
            "document": document_mcp_server
        }
        
        self.tool_registry = {}
        self._register_all_tools()
        
        logger.info("MCP Client initialized with all servers")
    
    def _register_all_tools(self):
        """Register tools from all MCP servers"""
        try:
            # Register HR tools
            for tool in self.servers["hr"].get_tools():
                self.tool_registry[f"hr_{tool.name}"] = {
                    "server": "hr",
                    "tool": tool,
                    "description": tool.description
                }
            
            # Register Finance tools
            for tool in self.servers["finance"].get_tools():
                self.tool_registry[f"finance_{tool.name}"] = {
                    "server": "finance",
                    "tool": tool,
                    "description": tool.description
                }
            
            # Register Document tools
            for tool in self.servers["document"].get_tools():
                self.tool_registry[f"document_{tool.name}"] = {
                    "server": "document",
                    "tool": tool,
                    "description": tool.description
                }
            
            logger.info(f"Registered {len(self.tool_registry)} MCP tools")
            
        except Exception as e:
            logger.error(f"Error registering MCP tools: {str(e)}")
            raise
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific MCP tool"""
        try:
            if tool_name not in self.tool_registry:
                return {
                    "error": f"Tool '{tool_name}' not found",
                    "available_tools": list(self.tool_registry.keys())
                }
            
            tool_info = self.tool_registry[tool_name]
            server_name = tool_info["server"]
            server = self.servers[server_name]
            
            # Extract the actual tool name (remove server prefix)
            actual_tool_name = tool_name.replace(f"{server_name}_", "")
            
            # Call the tool on the appropriate server with timeout
            try:
                if server_name == "hr":
                    result = await asyncio.wait_for(
                        self._call_hr_tool(actual_tool_name, arguments),
                        timeout=30.0
                    )
                elif server_name == "finance":
                    result = await asyncio.wait_for(
                        self._call_finance_tool(actual_tool_name, arguments),
                        timeout=30.0
                    )
                elif server_name == "document":
                    result = await asyncio.wait_for(
                        self._call_document_tool(actual_tool_name, arguments),
                        timeout=30.0
                    )
                else:
                    result = {"error": f"Unknown server: {server_name}"}
            except asyncio.TimeoutError:
                logger.error(f"Tool call timeout for {tool_name}")
                result = {"error": f"Tool call timeout for {tool_name}"}
            
            return {
                "tool_name": tool_name,
                "server": server_name,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {str(e)}")
            return {
                "error": f"Failed to call tool {tool_name}: {str(e)}",
                "tool_name": tool_name
            }
    
    async def _call_hr_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call HR MCP server tool"""
        try:
            server = self.servers["hr"].server

            # Use FastMCP's call_tool method
            result = await server.call_tool(tool_name, arguments)

            # Handle TextContent objects and other MCP types
            if hasattr(result, 'text'):
                # This is a TextContent object
                return result.text
            elif hasattr(result, '__dict__'):
                # Convert object to dict and then to JSON
                result_dict = {}
                for key, value in result.__dict__.items():
                    if hasattr(value, 'text'):
                        result_dict[key] = value.text
                    elif isinstance(value, (str, int, float, bool, list, dict)):
                        result_dict[key] = value
                    else:
                        result_dict[key] = str(value)
                return json.dumps(result_dict)
            elif isinstance(result, str):
                return result
            else:
                return json.dumps(result)

        except Exception as e:
            logger.error(f"Error calling HR tool {tool_name}: {str(e)}")
            return json.dumps({"error": f"Failed to call HR tool: {str(e)}"})
    
    async def _call_finance_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call Finance MCP server tool"""
        try:
            server = self.servers["finance"].server

            # Use FastMCP's call_tool method
            result = await server.call_tool(tool_name, arguments)

            # Handle TextContent objects and other MCP types
            if hasattr(result, 'text'):
                # This is a TextContent object
                return result.text
            elif hasattr(result, '__dict__'):
                # Convert object to dict and then to JSON
                result_dict = {}
                for key, value in result.__dict__.items():
                    if hasattr(value, 'text'):
                        result_dict[key] = value.text
                    elif isinstance(value, (str, int, float, bool, list, dict)):
                        result_dict[key] = value
                    else:
                        result_dict[key] = str(value)
                return json.dumps(result_dict)
            elif isinstance(result, str):
                return result
            else:
                return json.dumps(result)

        except Exception as e:
            logger.error(f"Error calling Finance tool {tool_name}: {str(e)}")
            return json.dumps({"error": f"Failed to call Finance tool: {str(e)}"})

    async def _call_document_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call Document MCP server tool"""
        try:
            server = self.servers["document"].server

            # Use FastMCP's call_tool method
            result = await server.call_tool(tool_name, arguments)

            # Handle TextContent objects and other MCP types
            if hasattr(result, 'text'):
                # This is a TextContent object
                return result.text
            elif hasattr(result, '__dict__'):
                # Convert object to dict and then to JSON
                result_dict = {}
                for key, value in result.__dict__.items():
                    if hasattr(value, 'text'):
                        result_dict[key] = value.text
                    elif isinstance(value, (str, int, float, bool, list, dict)):
                        result_dict[key] = value
                    else:
                        result_dict[key] = str(value)
                return json.dumps(result_dict)
            elif isinstance(result, str):
                return result
            else:
                return json.dumps(result)

        except Exception as e:
            logger.error(f"Error calling Document tool {tool_name}: {str(e)}")
            return json.dumps({"error": f"Failed to call Document tool: {str(e)}"})
    
    def get_available_tools(self, user_role: str = None) -> List[Dict[str, Any]]:
        """Get list of available tools, optionally filtered by user role"""
        try:
            tools = []
            
            for tool_name, tool_info in self.tool_registry.items():
                tool_data = {
                    "name": tool_name,
                    "server": tool_info["server"],
                    "description": tool_info["description"],
                    "schema": tool_info["tool"].inputSchema
                }
                
                # Add role-based filtering if needed
                if user_role:
                    # Check if user has access to this tool based on role
                    if self._check_tool_access(tool_name, user_role):
                        tools.append(tool_data)
                else:
                    tools.append(tool_data)
            
            return tools
            
        except Exception as e:
            logger.error(f"Error getting available tools: {str(e)}")
            return []
    
    def _check_tool_access(self, tool_name: str, user_role: str) -> bool:
        """Check if user role has access to specific tool"""
        try:
            # Define role-based tool access
            role_tool_access = {
                "EMPLOYEE": ["document_search_documents", "document_list_documents"],
                "HR": ["hr_", "document_"],  # HR can access all HR and document tools
                "FINANCE": ["finance_", "document_"],  # Finance can access all finance and document tools
                "MARKETING": ["document_"],  # Marketing can access document tools
                "ENGINEERING": ["document_"],  # Engineering can access document tools
                "CEO": ["hr_", "finance_", "document_"]  # CEO can access all tools
            }
            
            allowed_prefixes = role_tool_access.get(user_role.upper(), [])
            
            return any(tool_name.startswith(prefix) for prefix in allowed_prefixes)
            
        except Exception as e:
            logger.error(f"Error checking tool access: {str(e)}")
            return False
    
    async def query_with_context(self, query: str, user_role: str, department: str = None) -> Dict[str, Any]:
        """Intelligent query routing to appropriate MCP tools"""
        try:
            # Analyze query to determine which tools to use
            tools_to_call = self._analyze_query(query, user_role)
            
            results = []
            
            for tool_call in tools_to_call:
                tool_name = tool_call["tool"]
                arguments = tool_call["arguments"]
                
                # Add user context to arguments
                arguments["user_role"] = user_role
                if department:
                    arguments["department"] = department
                
                # Call the tool
                result = await self.call_tool(tool_name, arguments)
                results.append(result)
            
            return {
                "query": query,
                "user_role": user_role,
                "department": department,
                "tools_called": len(results),
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in query_with_context: {str(e)}")
            return {
                "error": f"Failed to process query: {str(e)}",
                "query": query
            }
    
    def _analyze_query(self, query: str, user_role: str) -> List[Dict[str, Any]]:
        """Analyze query to determine which MCP tools to call"""
        try:
            query_lower = query.lower()
            tools_to_call = []
            
            # HR-related queries
            if any(keyword in query_lower for keyword in ["employee", "staff", "hr", "performance", "leave", "attendance"]):
                if user_role.upper() in ["HR", "CEO"]:
                    if "count" in query_lower or "how many" in query_lower:
                        tools_to_call.append({
                            "tool": "hr_get_employee_count",
                            "arguments": {}
                        })
                    if "performance" in query_lower:
                        tools_to_call.append({
                            "tool": "hr_get_performance_metrics",
                            "arguments": {}
                        })
                    if "leave" in query_lower:
                        tools_to_call.append({
                            "tool": "hr_get_leave_summary",
                            "arguments": {}
                        })
            
            # Finance-related queries
            if any(keyword in query_lower for keyword in ["finance", "budget", "expense", "revenue", "financial", "quarterly"]):
                if user_role.upper() in ["FINANCE", "CEO"]:
                    if "quarterly" in query_lower or "report" in query_lower:
                        tools_to_call.append({
                            "tool": "finance_get_quarterly_report",
                            "arguments": {}
                        })
                    if "expense" in query_lower:
                        tools_to_call.append({
                            "tool": "finance_get_expense_analysis",
                            "arguments": {}
                        })
                    if "budget" in query_lower:
                        tools_to_call.append({
                            "tool": "finance_get_budget_status",
                            "arguments": {}
                        })
                    if "revenue" in query_lower:
                        tools_to_call.append({
                            "tool": "finance_get_revenue_metrics",
                            "arguments": {}
                        })
            
            # Document-related queries
            if any(keyword in query_lower for keyword in ["document", "policy", "handbook", "search", "file"]):
                tools_to_call.append({
                    "tool": "document_search_documents",
                    "arguments": {"query": query}
                })
            
            # If no specific tools identified, default to document search
            if not tools_to_call:
                tools_to_call.append({
                    "tool": "document_search_documents",
                    "arguments": {"query": query}
                })
            
            return tools_to_call
            
        except Exception as e:
            logger.error(f"Error analyzing query: {str(e)}")
            return []


# Create global instance
mcp_client = MCPClient()
