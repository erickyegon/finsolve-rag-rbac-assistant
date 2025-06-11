"""
Finance MCP Server for FinSolve RBAC Chatbot
Implements MCP server for financial data access with role-based permissions.

Author: Dr. Erick K. Yegon
Version: 1.0.0
"""

import asyncio
import json
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from mcp.server import FastMCP
from mcp.types import Tool, TextContent, Resource
from loguru import logger

from ...core.config import UserRole, ROLE_PERMISSIONS


class FinanceMCPServer:
    """MCP Server for Finance data operations"""
    
    def __init__(self, data_directory: str = "data"):
        self.server = FastMCP("finance-data-server")
        self.data_directory = Path(data_directory)
        self.finance_dir = self.data_directory / "finance"
        
        # Register tools
        self._register_tools()
        
        logger.info("Finance MCP Server initialized")
    
    def _register_tools(self):
        """Register MCP tools for Finance operations"""
        
        @self.server.tool()
        async def get_quarterly_report(user_role: str, quarter: Optional[str] = None, year: Optional[int] = None) -> str:
            """Get quarterly financial report with role-based access control"""
            try:
                # Check permissions
                if not self._check_permission(user_role, "financial_data"):
                    return json.dumps({
                        "error": "Access denied: Insufficient permissions for financial data",
                        "required_role": "FINANCE or CEO"
                    })
                
                # Load quarterly financial report
                report_path = self.finance_dir / "quarterly_financial_report.md"
                if not report_path.exists():
                    return json.dumps({"error": "Quarterly financial report not found"})
                
                content = report_path.read_text(encoding='utf-8')
                
                # Parse content for specific quarter if requested
                if quarter and year:
                    # Extract specific quarter data
                    quarter_section = self._extract_quarter_data(content, quarter, year)
                    if quarter_section:
                        return json.dumps({
                            "quarter": f"Q{quarter} {year}",
                            "data": quarter_section,
                            "access_level": user_role
                        })
                    else:
                        return json.dumps({
                            "error": f"Data for Q{quarter} {year} not found",
                            "available_data": "Q1-Q4 2024"
                        })
                
                # Return full report
                return json.dumps({
                    "report_type": "Full Quarterly Financial Report",
                    "content": content,
                    "access_level": user_role,
                    "last_updated": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error in get_quarterly_report: {str(e)}")
                return json.dumps({"error": f"Failed to retrieve quarterly report: {str(e)}"})
        
        @self.server.tool()
        async def get_expense_analysis(user_role: str, category: Optional[str] = None, 
                                     time_period: Optional[str] = None) -> str:
            """Get expense analysis with detailed breakdown"""
            try:
                # Check permissions
                if not self._check_permission(user_role, "expense_data"):
                    return json.dumps({
                        "error": "Access denied: Insufficient permissions for expense data",
                        "required_role": "FINANCE or CEO"
                    })
                
                # Load expense report
                expense_path = self.finance_dir / "expense_report.md"
                if not expense_path.exists():
                    return json.dumps({"error": "Expense report not found"})
                
                content = expense_path.read_text(encoding='utf-8')
                
                # Parse expense data
                expense_data = self._parse_expense_data(content)
                
                # Filter by category if specified
                if category:
                    category_data = expense_data.get('categories', {}).get(category.lower())
                    if category_data:
                        return json.dumps({
                            "category": category,
                            "expense_data": category_data,
                            "time_period": time_period or "Latest available",
                            "access_level": user_role
                        })
                    else:
                        available_categories = list(expense_data.get('categories', {}).keys())
                        return json.dumps({
                            "error": f"Category '{category}' not found",
                            "available_categories": available_categories
                        })
                
                # Return full expense analysis
                return json.dumps({
                    "expense_analysis": expense_data,
                    "access_level": user_role,
                    "time_period": time_period or "Latest available"
                })
                
            except Exception as e:
                logger.error(f"Error in get_expense_analysis: {str(e)}")
                return json.dumps({"error": f"Failed to retrieve expense analysis: {str(e)}"})
        
        @self.server.tool()
        async def get_budget_status(user_role: str, department: Optional[str] = None) -> str:
            """Get budget status and variance analysis"""
            try:
                # Check permissions
                if not self._check_permission(user_role, "budget_data"):
                    return json.dumps({
                        "error": "Access denied: Insufficient permissions for budget data",
                        "required_role": "FINANCE or CEO"
                    })
                
                # Load budget data from financial reports
                report_path = self.finance_dir / "quarterly_financial_report.md"
                if not report_path.exists():
                    return json.dumps({"error": "Financial report not found"})
                
                content = report_path.read_text(encoding='utf-8')
                
                # Extract budget information
                budget_data = self._extract_budget_data(content)
                
                # Filter by department if specified
                if department:
                    dept_budget = budget_data.get('departments', {}).get(department.lower())
                    if dept_budget:
                        return json.dumps({
                            "department": department,
                            "budget_data": dept_budget,
                            "access_level": user_role
                        })
                    else:
                        available_depts = list(budget_data.get('departments', {}).keys())
                        return json.dumps({
                            "error": f"Budget data for '{department}' not found",
                            "available_departments": available_depts
                        })
                
                # Return full budget status
                return json.dumps({
                    "budget_status": budget_data,
                    "access_level": user_role,
                    "last_updated": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error in get_budget_status: {str(e)}")
                return json.dumps({"error": f"Failed to retrieve budget status: {str(e)}"})
        
        @self.server.tool()
        async def get_revenue_metrics(user_role: str, metric_type: Optional[str] = None) -> str:
            """Get revenue metrics and growth analysis"""
            try:
                # Check permissions
                if not self._check_permission(user_role, "revenue_data"):
                    return json.dumps({
                        "error": "Access denied: Insufficient permissions for revenue data",
                        "required_role": "FINANCE or CEO"
                    })
                
                # Load financial report
                report_path = self.finance_dir / "quarterly_financial_report.md"
                if not report_path.exists():
                    return json.dumps({"error": "Financial report not found"})
                
                content = report_path.read_text(encoding='utf-8')
                
                # Extract revenue metrics
                revenue_data = self._extract_revenue_data(content)
                
                # Filter by metric type if specified
                if metric_type:
                    metric_data = revenue_data.get(metric_type.lower())
                    if metric_data:
                        return json.dumps({
                            "metric_type": metric_type,
                            "data": metric_data,
                            "access_level": user_role
                        })
                    else:
                        available_metrics = list(revenue_data.keys())
                        return json.dumps({
                            "error": f"Metric type '{metric_type}' not found",
                            "available_metrics": available_metrics
                        })
                
                # Return full revenue metrics
                return json.dumps({
                    "revenue_metrics": revenue_data,
                    "access_level": user_role,
                    "last_updated": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error in get_revenue_metrics: {str(e)}")
                return json.dumps({"error": f"Failed to retrieve revenue metrics: {str(e)}"})
    
    def _check_permission(self, user_role: str, data_type: str) -> bool:
        """Check if user role has permission for specific data type"""
        try:
            role = UserRole(user_role.lower())

            # CEO has access to all financial data
            if role == UserRole.CEO:
                return True

            # Finance role has access to all financial data
            if role == UserRole.FINANCE:
                return True

            # System Admin has NO access to business data (HR, Finance, etc.)
            if role == UserRole.SYSTEM_ADMIN:
                return False

            # Other roles don't have access to financial data
            return False

        except (ValueError, AttributeError):
            return False
    
    def _extract_quarter_data(self, content: str, quarter: str, year: int) -> Optional[str]:
        """Extract specific quarter data from financial report"""
        try:
            lines = content.split('\n')
            quarter_header = f"Q{quarter} {year}"
            
            start_idx = None
            for i, line in enumerate(lines):
                if quarter_header in line:
                    start_idx = i
                    break
            
            if start_idx is None:
                return None
            
            # Extract section until next quarter or end
            end_idx = len(lines)
            for i in range(start_idx + 1, len(lines)):
                if lines[i].startswith('## Q') and lines[i] != lines[start_idx]:
                    end_idx = i
                    break
            
            return '\n'.join(lines[start_idx:end_idx])
            
        except Exception as e:
            logger.error(f"Error extracting quarter data: {str(e)}")
            return None
    
    def _parse_expense_data(self, content: str) -> Dict[str, Any]:
        """Parse expense data from content"""
        try:
            # This is a simplified parser - in production, you'd use more sophisticated parsing
            expense_data = {
                "categories": {
                    "personnel": {"amount": 0, "percentage": 0},
                    "technology": {"amount": 0, "percentage": 0},
                    "marketing": {"amount": 0, "percentage": 0},
                    "operations": {"amount": 0, "percentage": 0}
                },
                "total_expenses": 0,
                "variance_analysis": {}
            }
            
            # Extract expense information from content
            lines = content.split('\n')
            for line in lines:
                if 'expense' in line.lower() or 'cost' in line.lower():
                    # Parse expense data (simplified)
                    pass
            
            return expense_data
            
        except Exception as e:
            logger.error(f"Error parsing expense data: {str(e)}")
            return {"error": "Failed to parse expense data"}
    
    def _extract_budget_data(self, content: str) -> Dict[str, Any]:
        """Extract budget data from financial report"""
        try:
            budget_data = {
                "total_budget": 0,
                "spent_to_date": 0,
                "remaining_budget": 0,
                "variance_percentage": 0,
                "departments": {}
            }
            
            # Parse budget information from content
            # This is simplified - in production, use more sophisticated parsing
            
            return budget_data
            
        except Exception as e:
            logger.error(f"Error extracting budget data: {str(e)}")
            return {"error": "Failed to extract budget data"}
    
    def _extract_revenue_data(self, content: str) -> Dict[str, Any]:
        """Extract revenue data from financial report"""
        try:
            revenue_data = {
                "quarterly_revenue": {},
                "growth_rate": 0,
                "revenue_streams": {},
                "projections": {}
            }
            
            # Parse revenue information from content
            # This is simplified - in production, use more sophisticated parsing
            
            return revenue_data
            
        except Exception as e:
            logger.error(f"Error extracting revenue data: {str(e)}")
            return {"error": "Failed to extract revenue data"}
    
    async def start(self):
        """Start the MCP server"""
        try:
            await self.server.run()
            logger.info("Finance MCP Server started successfully")
        except Exception as e:
            logger.error(f"Failed to start Finance MCP Server: {str(e)}")
            raise
    
    def get_tools(self) -> List[Tool]:
        """Get list of available tools"""
        return [
            Tool(
                name="get_quarterly_report",
                description="Get quarterly financial report with role-based access control",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_role": {"type": "string", "description": "User role (FINANCE, C_LEVEL, etc.)"},
                        "quarter": {"type": "string", "description": "Optional quarter (1-4)"},
                        "year": {"type": "integer", "description": "Optional year"}
                    },
                    "required": ["user_role"]
                }
            ),
            Tool(
                name="get_expense_analysis",
                description="Get expense analysis with detailed breakdown",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_role": {"type": "string", "description": "User role (FINANCE, C_LEVEL, etc.)"},
                        "category": {"type": "string", "description": "Optional expense category"},
                        "time_period": {"type": "string", "description": "Optional time period"}
                    },
                    "required": ["user_role"]
                }
            ),
            Tool(
                name="get_budget_status",
                description="Get budget status and variance analysis",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_role": {"type": "string", "description": "User role (FINANCE, C_LEVEL, etc.)"},
                        "department": {"type": "string", "description": "Optional department filter"}
                    },
                    "required": ["user_role"]
                }
            ),
            Tool(
                name="get_revenue_metrics",
                description="Get revenue metrics and growth analysis",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_role": {"type": "string", "description": "User role (FINANCE, C_LEVEL, etc.)"},
                        "metric_type": {"type": "string", "description": "Optional metric type"}
                    },
                    "required": ["user_role"]
                }
            )
        ]


# Create global instance
finance_mcp_server = FinanceMCPServer()
