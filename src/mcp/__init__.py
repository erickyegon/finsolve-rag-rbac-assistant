"""
MCP (Model Context Protocol) Integration for FinSolve RBAC Chatbot
Implements true MCP servers and tools for structured data access.

Author: Dr. Erick K. Yegon
Version: 1.0.0
"""

from .servers.hr_server import HRMCPServer
from .servers.finance_server import FinanceMCPServer
from .servers.document_server import DocumentMCPServer
from .client.mcp_client import MCPClient
from .tools.mcp_tools import MCPToolRegistry

__all__ = [
    "HRMCPServer",
    "FinanceMCPServer", 
    "DocumentMCPServer",
    "MCPClient",
    "MCPToolRegistry"
]
