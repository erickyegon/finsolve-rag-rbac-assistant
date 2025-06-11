"""
MCP Tools Registry for FinSolve RBAC Chatbot
Provides LangChain-compatible tools that interface with MCP servers.

Author: Dr. Erick K. Yegon
Version: 1.0.0
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Type
from datetime import datetime

from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolUse
from pydantic import BaseModel, Field
from loguru import logger

from ..client.mcp_client import mcp_client


class MCPToolInput(BaseModel):
    """Input schema for MCP tools"""
    query: str = Field(description="The query or request to process")
    user_role: str = Field(description="User role for access control")
    department: Optional[str] = Field(default=None, description="Optional department filter")
    additional_params: Optional[Dict[str, Any]] = Field(default=None, description="Additional parameters")


class MCPQueryTool(BaseTool):
    """LangChain tool that interfaces with MCP servers"""
    
    name: str = "mcp_query"
    description: str = "Query FinSolve company data using MCP (Model Context Protocol) servers with role-based access control"
    args_schema: Type[BaseModel] = MCPToolInput
    
    def _run(
        self,
        query: str,
        user_role: str,
        department: Optional[str] = None,
        additional_params: Optional[Dict[str, Any]] = None,
        run_manager: Optional[CallbackManagerForToolUse] = None,
    ) -> str:
        """Execute the MCP query synchronously"""
        try:
            # Run the async query in a sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    mcp_client.query_with_context(query, user_role, department)
                )
                return self._format_result(result)
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error in MCP query tool: {str(e)}")
            return f"Error processing query: {str(e)}"
    
    async def _arun(
        self,
        query: str,
        user_role: str,
        department: Optional[str] = None,
        additional_params: Optional[Dict[str, Any]] = None,
        run_manager: Optional[CallbackManagerForToolUse] = None,
    ) -> str:
        """Execute the MCP query asynchronously"""
        try:
            result = await mcp_client.query_with_context(query, user_role, department)
            return self._format_result(result)
            
        except Exception as e:
            logger.error(f"Error in async MCP query tool: {str(e)}")
            return f"Error processing query: {str(e)}"
    
    def _format_result(self, result: Dict[str, Any]) -> str:
        """Format MCP result for LangChain consumption"""
        try:
            if "error" in result:
                return f"Error: {result['error']}"
            
            formatted_results = []
            
            for tool_result in result.get("results", []):
                if "result" in tool_result:
                    # Parse JSON result if it's a string
                    if isinstance(tool_result["result"], str):
                        try:
                            parsed_result = json.loads(tool_result["result"])
                            formatted_results.append(self._format_parsed_result(parsed_result, tool_result.get("tool_name", "")))
                        except json.JSONDecodeError:
                            formatted_results.append(tool_result["result"])
                    else:
                        formatted_results.append(str(tool_result["result"]))
            
            if formatted_results:
                return "\n\n".join(formatted_results)
            else:
                return "No results found for the query."
                
        except Exception as e:
            logger.error(f"Error formatting MCP result: {str(e)}")
            return f"Error formatting result: {str(e)}"
    
    def _format_parsed_result(self, parsed_result: Dict[str, Any], tool_name: str) -> str:
        """Format parsed JSON result into readable text"""
        try:
            if "error" in parsed_result:
                return f"Error from {tool_name}: {parsed_result['error']}"
            
            # Format based on tool type
            if "hr_" in tool_name:
                return self._format_hr_result(parsed_result)
            elif "finance_" in tool_name:
                return self._format_finance_result(parsed_result)
            elif "document_" in tool_name:
                return self._format_document_result(parsed_result)
            else:
                return json.dumps(parsed_result, indent=2)
                
        except Exception as e:
            logger.error(f"Error formatting parsed result: {str(e)}")
            return str(parsed_result)
    
    def _format_hr_result(self, result: Dict[str, Any]) -> str:
        """Format HR-specific results"""
        try:
            formatted = []
            
            if "total_employees" in result:
                formatted.append(f"**Total Employees:** {result['total_employees']}")
                
                if "department_breakdown" in result:
                    formatted.append("\n**Department Breakdown:**")
                    for dept, count in result["department_breakdown"].items():
                        formatted.append(f"- {dept}: {count} employees")
            
            if "employee" in result:
                emp = result["employee"]
                formatted.append(f"**Employee Details:**")
                formatted.append(f"- Name: {emp.get('full_name', 'N/A')}")
                formatted.append(f"- Role: {emp.get('role', 'N/A')}")
                formatted.append(f"- Department: {emp.get('department', 'N/A')}")
                formatted.append(f"- Email: {emp.get('email', 'N/A')}")
            
            if "average_performance_rating" in result:
                formatted.append(f"**Performance Metrics:**")
                formatted.append(f"- Average Rating: {result['average_performance_rating']:.2f}/5")
                formatted.append(f"- Total Employees Analyzed: {result.get('total_employees_analyzed', 0)}")
                
                if "top_performers" in result and result["top_performers"]:
                    formatted.append("\n**Top Performers:**")
                    for performer in result["top_performers"][:5]:  # Show top 5
                        formatted.append(f"- {performer.get('full_name', 'N/A')} ({performer.get('department', 'N/A')}): {performer.get('performance_rating', 'N/A')}/5")
            
            if "average_leave_balance" in result:
                formatted.append(f"**Leave Summary:**")
                formatted.append(f"- Average Leave Balance: {result['average_leave_balance']:.1f} days")
                formatted.append(f"- Average Leaves Taken: {result['average_leaves_taken']:.1f} days")
                formatted.append(f"- Leave Utilization Rate: {result.get('leave_utilization_rate', 0):.1f}%")
            
            return "\n".join(formatted) if formatted else str(result)
            
        except Exception as e:
            logger.error(f"Error formatting HR result: {str(e)}")
            return str(result)
    
    def _format_finance_result(self, result: Dict[str, Any]) -> str:
        """Format Finance-specific results"""
        try:
            formatted = []
            
            if "report_type" in result:
                formatted.append(f"**{result['report_type']}**")
                if "content" in result:
                    # Extract key financial metrics from content
                    content = result["content"]
                    if "revenue" in content.lower():
                        formatted.append("\n**Key Financial Highlights:**")
                        # Parse content for key metrics (simplified)
                        lines = content.split('\n')
                        for line in lines[:10]:  # Show first 10 lines
                            if line.strip() and not line.startswith('#'):
                                formatted.append(f"- {line.strip()}")
            
            if "expense_analysis" in result:
                exp_data = result["expense_analysis"]
                formatted.append("**Expense Analysis:**")
                if "total_expenses" in exp_data:
                    formatted.append(f"- Total Expenses: ${exp_data['total_expenses']:,}")
                if "categories" in exp_data:
                    formatted.append("\n**Expense Categories:**")
                    for category, data in exp_data["categories"].items():
                        if isinstance(data, dict) and "amount" in data:
                            formatted.append(f"- {category.title()}: ${data['amount']:,}")
            
            if "budget_status" in result:
                budget_data = result["budget_status"]
                formatted.append("**Budget Status:**")
                if "total_budget" in budget_data:
                    formatted.append(f"- Total Budget: ${budget_data['total_budget']:,}")
                if "spent_to_date" in budget_data:
                    formatted.append(f"- Spent to Date: ${budget_data['spent_to_date']:,}")
                if "remaining_budget" in budget_data:
                    formatted.append(f"- Remaining Budget: ${budget_data['remaining_budget']:,}")
            
            if "revenue_metrics" in result:
                rev_data = result["revenue_metrics"]
                formatted.append("**Revenue Metrics:**")
                if "growth_rate" in rev_data:
                    formatted.append(f"- Growth Rate: {rev_data['growth_rate']}%")
                if "quarterly_revenue" in rev_data:
                    formatted.append("\n**Quarterly Revenue:**")
                    for quarter, revenue in rev_data["quarterly_revenue"].items():
                        formatted.append(f"- {quarter}: ${revenue:,}")
            
            return "\n".join(formatted) if formatted else str(result)
            
        except Exception as e:
            logger.error(f"Error formatting Finance result: {str(e)}")
            return str(result)
    
    def _format_document_result(self, result: Dict[str, Any]) -> str:
        """Format Document-specific results"""
        try:
            formatted = []
            
            if "results" in result:
                search_results = result["results"]
                formatted.append(f"**Document Search Results:** ({len(search_results)} found)")
                
                for doc in search_results[:5]:  # Show top 5 results
                    formatted.append(f"\n**{doc.get('filename', 'Unknown')}**")
                    formatted.append(f"- Department: {doc.get('department', 'N/A')}")
                    formatted.append(f"- Type: {doc.get('document_type', 'N/A')}")
                    if "content_preview" in doc:
                        preview = doc["content_preview"][:200] + "..." if len(doc["content_preview"]) > 200 else doc["content_preview"]
                        formatted.append(f"- Preview: {preview}")
            
            if "documents" in result:
                docs = result["documents"]
                formatted.append(f"**Document List:** ({len(docs)} documents)")
                
                for doc in docs[:10]:  # Show top 10 documents
                    formatted.append(f"- {doc.get('filename', 'Unknown')} ({doc.get('department', 'N/A')})")
            
            if "content" in result:
                formatted.append("**Document Content:**")
                content = result["content"]
                if len(content) > 1000:
                    formatted.append(content[:1000] + "... [Content truncated]")
                else:
                    formatted.append(content)
            
            if "summary" in result:
                formatted.append("**Document Summary:**")
                formatted.append(result["summary"])
            
            return "\n".join(formatted) if formatted else str(result)
            
        except Exception as e:
            logger.error(f"Error formatting Document result: {str(e)}")
            return str(result)


class MCPToolRegistry:
    """Registry for MCP-based LangChain tools"""
    
    def __init__(self):
        self.tools = {
            "mcp_query": MCPQueryTool()
        }
        
        logger.info("MCP Tool Registry initialized")
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a specific MCP tool"""
        return self.tools.get(tool_name)
    
    def get_all_tools(self) -> List[BaseTool]:
        """Get all available MCP tools"""
        return list(self.tools.values())
    
    def get_tools_for_role(self, user_role: str) -> List[BaseTool]:
        """Get tools available for specific user role"""
        try:
            from ...core.config import UserRole
            role = UserRole(user_role.lower())

            # CEO has access to all business tools
            if role == UserRole.CEO:
                return self.get_all_tools()

            # System Admin has NO access to business tools (only system management)
            if role == UserRole.SYSTEM_ADMIN:
                return []  # No MCP business tools for system admin

            # HR has access to HR tools only
            if role == UserRole.HR:
                return [tool for tool in self.get_all_tools() if "hr_" in tool.name]

            # Finance has access to Finance tools only
            if role == UserRole.FINANCE:
                return [tool for tool in self.get_all_tools() if "finance_" in tool.name]

            # Other roles have access to document tools only
            return [tool for tool in self.get_all_tools() if "document_" in tool.name]

        except (ValueError, AttributeError):
            # Default to document tools only for unknown roles
            return [tool for tool in self.get_all_tools() if "document_" in tool.name]


# Create global instance
mcp_tool_registry = MCPToolRegistry()
