"""
HR MCP Server for FinSolve RBAC Chatbot
Implements MCP server for HR data access with role-based permissions.

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
from ...data.processors import data_processor


class HRMCPServer:
    """MCP Server for HR data operations"""

    def __init__(self, data_directory: str = "data"):
        self.server = FastMCP("hr-data-server")
        self.data_directory = Path(data_directory)
        self.hr_data_path = self.data_directory / "hr" / "hr_data.csv"

        # Register tools
        self._register_tools()

        logger.info("HR MCP Server initialized")

    def _register_tools(self):
        """Register MCP tools for HR operations"""

        @self.server.tool()
        async def get_employee_count(user_role: str, department: Optional[str] = None) -> str:
            """Get employee count by department with role-based access control"""
            try:
                # Check permissions
                if not self._check_permission(user_role, "employee_data"):
                    return json.dumps({
                        "error": "Access denied: Insufficient permissions for employee data",
                        "required_role": "HR or CEO"
                    })
                
                # Load HR data
                if not self.hr_data_path.exists():
                    return json.dumps({"error": "HR data file not found"})
                
                df = pd.read_csv(self.hr_data_path)
                
                if department:
                    # Filter by department
                    dept_df = df[df['department'].str.lower() == department.lower()]
                    if dept_df.empty:
                        return json.dumps({
                            "department": department,
                            "employee_count": 0,
                            "message": f"No employees found in {department} department"
                        })
                    
                    return json.dumps({
                        "department": department,
                        "employee_count": len(dept_df),
                        "employees": dept_df[['full_name', 'role', 'email']].to_dict('records')
                    })
                else:
                    # Get count by all departments
                    dept_counts = df['department'].value_counts().to_dict()
                    total_employees = len(df)
                    
                    return json.dumps({
                        "total_employees": total_employees,
                        "department_breakdown": dept_counts,
                        "departments": list(dept_counts.keys())
                    })
                    
            except Exception as e:
                logger.error(f"Error in get_employee_count: {str(e)}")
                return json.dumps({"error": f"Failed to retrieve employee count: {str(e)}"})
        
        @self.server.tool()
        async def get_employee_details(user_role: str, employee_id: Optional[str] = None, 
                                     department: Optional[str] = None) -> str:
            """Get detailed employee information with role-based filtering"""
            try:
                # Check permissions
                if not self._check_permission(user_role, "employee_details"):
                    return json.dumps({
                        "error": "Access denied: Insufficient permissions for detailed employee data",
                        "required_role": "HR or CEO"
                    })
                
                # Load HR data
                if not self.hr_data_path.exists():
                    return json.dumps({"error": "HR data file not found"})
                
                df = pd.read_csv(self.hr_data_path)
                
                if employee_id:
                    # Get specific employee
                    employee = df[df['employee_id'] == employee_id]
                    if employee.empty:
                        return json.dumps({"error": f"Employee {employee_id} not found"})
                    
                    # Apply role-based filtering
                    employee_data = employee.iloc[0].to_dict()
                    filtered_data = self._filter_employee_data(employee_data, user_role)
                    
                    return json.dumps({
                        "employee": filtered_data,
                        "data_access_level": user_role
                    })
                
                elif department:
                    # Get employees by department
                    dept_employees = df[df['department'].str.lower() == department.lower()]
                    if dept_employees.empty:
                        return json.dumps({
                            "department": department,
                            "employees": [],
                            "message": f"No employees found in {department} department"
                        })
                    
                    # Apply role-based filtering to all employees
                    filtered_employees = []
                    for _, emp in dept_employees.iterrows():
                        filtered_emp = self._filter_employee_data(emp.to_dict(), user_role)
                        filtered_employees.append(filtered_emp)
                    
                    return json.dumps({
                        "department": department,
                        "employee_count": len(filtered_employees),
                        "employees": filtered_employees,
                        "data_access_level": user_role
                    })
                
                else:
                    return json.dumps({
                        "error": "Please specify either employee_id or department",
                        "usage": "get_employee_details(user_role, employee_id='FINEMP1001') or get_employee_details(user_role, department='Finance')"
                    })
                    
            except Exception as e:
                logger.error(f"Error in get_employee_details: {str(e)}")
                return json.dumps({"error": f"Failed to retrieve employee details: {str(e)}"})
        
        @self.server.tool()
        async def get_performance_metrics(user_role: str, department: Optional[str] = None) -> str:
            """Get performance metrics with role-based access"""
            try:
                # Check permissions
                if not self._check_permission(user_role, "performance_data"):
                    return json.dumps({
                        "error": "Access denied: Insufficient permissions for performance data",
                        "required_role": "HR or CEO"
                    })
                
                # Load HR data
                if not self.hr_data_path.exists():
                    return json.dumps({"error": "HR data file not found"})
                
                df = pd.read_csv(self.hr_data_path)
                
                if department:
                    df = df[df['department'].str.lower() == department.lower()]
                    if df.empty:
                        return json.dumps({
                            "department": department,
                            "message": f"No performance data found for {department} department"
                        })
                
                # Calculate performance metrics
                performance_stats = {
                    "average_performance_rating": float(df['performance_rating'].mean()),
                    "performance_distribution": df['performance_rating'].value_counts().to_dict(),
                    "top_performers": df[df['performance_rating'] >= 4][['full_name', 'department', 'performance_rating']].to_dict('records'),
                    "improvement_needed": df[df['performance_rating'] <= 2][['full_name', 'department', 'performance_rating']].to_dict('records'),
                    "average_attendance": float(df['attendance_pct'].mean()),
                    "total_employees_analyzed": len(df)
                }
                
                if department:
                    performance_stats["department"] = department
                
                return json.dumps(performance_stats)
                
            except Exception as e:
                logger.error(f"Error in get_performance_metrics: {str(e)}")
                return json.dumps({"error": f"Failed to retrieve performance metrics: {str(e)}"})
        
        @self.server.tool()
        async def get_leave_summary(user_role: str, department: Optional[str] = None) -> str:
            """Get leave balance and usage summary"""
            try:
                # Check permissions
                if not self._check_permission(user_role, "leave_data"):
                    return json.dumps({
                        "error": "Access denied: Insufficient permissions for leave data",
                        "required_role": "HR or CEO"
                    })
                
                # Load HR data
                if not self.hr_data_path.exists():
                    return json.dumps({"error": "HR data file not found"})
                
                df = pd.read_csv(self.hr_data_path)
                
                if department:
                    df = df[df['department'].str.lower() == department.lower()]
                    if df.empty:
                        return json.dumps({
                            "department": department,
                            "message": f"No leave data found for {department} department"
                        })
                
                # Calculate leave metrics
                leave_stats = {
                    "average_leave_balance": float(df['leave_balance'].mean()),
                    "average_leaves_taken": float(df['leaves_taken'].mean()),
                    "total_leave_days_available": int(df['leave_balance'].sum()),
                    "total_leave_days_used": int(df['leaves_taken'].sum()),
                    "employees_with_low_balance": len(df[df['leave_balance'] < 5]),
                    "employees_with_high_usage": len(df[df['leaves_taken'] > 15]),
                    "leave_utilization_rate": float((df['leaves_taken'] / (df['leave_balance'] + df['leaves_taken'])).mean() * 100)
                }
                
                if department:
                    leave_stats["department"] = department
                
                return json.dumps(leave_stats)
                
            except Exception as e:
                logger.error(f"Error in get_leave_summary: {str(e)}")
                return json.dumps({"error": f"Failed to retrieve leave summary: {str(e)}"})
    
    def _check_permission(self, user_role: str, data_type: str) -> bool:
        """Check if user role has permission for specific data type"""
        try:
            role = UserRole(user_role.lower())

            # CEO has access to all HR data
            if role == UserRole.CEO:
                return True

            # HR role has access to all HR data
            if role == UserRole.HR:
                return True

            # System Admin has NO access to business data (HR, Finance, etc.)
            if role == UserRole.SYSTEM_ADMIN:
                return False

            # Other roles don't have access to HR data
            return False

        except (ValueError, AttributeError):
            return False
    
    def _filter_employee_data(self, employee_data: Dict[str, Any], user_role: str) -> Dict[str, Any]:
        """Filter employee data based on user role"""
        try:
            role = UserRole(user_role.upper())
            
            # Base fields available to all authorized users
            base_fields = ['employee_id', 'full_name', 'role', 'department', 'email', 'location']
            
            # Additional fields for HR and CEO
            if role in [UserRole.HR, UserRole.CEO]:
                additional_fields = ['date_of_joining', 'manager_id', 'leave_balance', 'leaves_taken',
                                   'attendance_pct', 'performance_rating', 'last_review_date']
                allowed_fields = base_fields + additional_fields
            else:
                allowed_fields = base_fields

            # Filter data
            filtered_data = {k: v for k, v in employee_data.items() if k in allowed_fields}

            # Mask sensitive data for non-HR/CEO roles
            if role not in [UserRole.HR, UserRole.CEO]:
                if 'salary' in filtered_data:
                    del filtered_data['salary']
            
            return filtered_data
            
        except Exception as e:
            logger.error(f"Error filtering employee data: {str(e)}")
            return {"error": "Failed to filter employee data"}
    
    async def start(self):
        """Start the MCP server"""
        try:
            await self.server.run()
            logger.info("HR MCP Server started successfully")
        except Exception as e:
            logger.error(f"Failed to start HR MCP Server: {str(e)}")
            raise
    
    def get_tools(self) -> List[Tool]:
        """Get list of available tools"""
        return [
            Tool(
                name="get_employee_count",
                description="Get employee count by department with role-based access control",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_role": {"type": "string", "description": "User role (HR, C_LEVEL, etc.)"},
                        "department": {"type": "string", "description": "Optional department filter"}
                    },
                    "required": ["user_role"]
                }
            ),
            Tool(
                name="get_employee_details", 
                description="Get detailed employee information with role-based filtering",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_role": {"type": "string", "description": "User role (HR, C_LEVEL, etc.)"},
                        "employee_id": {"type": "string", "description": "Optional specific employee ID"},
                        "department": {"type": "string", "description": "Optional department filter"}
                    },
                    "required": ["user_role"]
                }
            ),
            Tool(
                name="get_performance_metrics",
                description="Get performance metrics with role-based access",
                inputSchema={
                    "type": "object", 
                    "properties": {
                        "user_role": {"type": "string", "description": "User role (HR, C_LEVEL, etc.)"},
                        "department": {"type": "string", "description": "Optional department filter"}
                    },
                    "required": ["user_role"]
                }
            ),
            Tool(
                name="get_leave_summary",
                description="Get leave balance and usage summary",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_role": {"type": "string", "description": "User role (HR, C_LEVEL, etc.)"},
                        "department": {"type": "string", "description": "Optional department filter"}
                    },
                    "required": ["user_role"]
                }
            )
        ]


# Create global instance
hr_mcp_server = HRMCPServer()
