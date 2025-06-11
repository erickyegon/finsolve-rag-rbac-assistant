"""
User Management System for System Administrators
Provides user creation, role management, and system administration functions.

Author: Dr. Erick K. Yegon
Version: 1.0.0
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from passlib.context import CryptContext
from loguru import logger

from ..core.config import UserRole, ROLE_PERMISSIONS
from ..auth.models import User, UserCreate, UserUpdate
from ..database.connection import get_db

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserManagementService:
    """Service for system administrator user management operations"""
    
    def __init__(self):
        self.logger = logger
        
    def check_admin_permission(self, user_role: str) -> bool:
        """Check if user has system administrator permissions"""
        try:
            role = UserRole(user_role.lower())
            return role == UserRole.SYSTEM_ADMIN
        except (ValueError, AttributeError):
            return False
    
    def create_user(self, admin_role: str, user_data: UserCreate, db: Session) -> Dict[str, Any]:
        """Create a new user (System Admin only)"""
        try:
            if not self.check_admin_permission(admin_role):
                return {
                    "success": False,
                    "error": "Access denied: System Administrator role required",
                    "required_role": "SYSTEM_ADMIN"
                }
            
            # Check if user already exists
            existing_user = db.query(User).filter(
                or_(User.email == user_data.email, User.username == user_data.username)
            ).first()
            
            if existing_user:
                return {
                    "success": False,
                    "error": "User already exists with this email or username"
                }
            
            # Hash password
            hashed_password = pwd_context.hash(user_data.password)
            
            # Create new user
            new_user = User(
                email=user_data.email,
                username=user_data.username,
                full_name=user_data.full_name,
                hashed_password=hashed_password,
                role=user_data.role,
                department=user_data.department,
                employee_id=user_data.employee_id,
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            self.logger.info(f"User created successfully: {new_user.email} with role {new_user.role}")
            
            return {
                "success": True,
                "message": "User created successfully",
                "user": {
                    "id": new_user.id,
                    "email": new_user.email,
                    "username": new_user.username,
                    "full_name": new_user.full_name,
                    "role": new_user.role.value,
                    "department": new_user.department,
                    "employee_id": new_user.employee_id,
                    "is_active": new_user.is_active,
                    "created_at": new_user.created_at.isoformat()
                }
            }
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error creating user: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to create user: {str(e)}"
            }
    
    def list_users(self, admin_role: str, db: Session, 
                   department: Optional[str] = None, 
                   role: Optional[str] = None,
                   active_only: bool = True) -> Dict[str, Any]:
        """List all users (System Admin only)"""
        try:
            if not self.check_admin_permission(admin_role):
                return {
                    "success": False,
                    "error": "Access denied: System Administrator role required",
                    "required_role": "SYSTEM_ADMIN"
                }
            
            # Build query
            query = db.query(User)
            
            if active_only:
                query = query.filter(User.is_active == True)
            
            if department:
                query = query.filter(User.department == department)
            
            if role:
                try:
                    user_role = UserRole(role.lower())
                    query = query.filter(User.role == user_role)
                except ValueError:
                    return {
                        "success": False,
                        "error": f"Invalid role: {role}"
                    }
            
            users = query.all()
            
            user_list = []
            for user in users:
                user_list.append({
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "role": user.role.value,
                    "department": user.department,
                    "employee_id": user.employee_id,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "last_login": user.last_login.isoformat() if user.last_login else None
                })
            
            return {
                "success": True,
                "users": user_list,
                "total_count": len(user_list),
                "filters": {
                    "department": department,
                    "role": role,
                    "active_only": active_only
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error listing users: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to list users: {str(e)}"
            }
    
    def update_user(self, admin_role: str, user_id: int, user_data: UserUpdate, db: Session) -> Dict[str, Any]:
        """Update user information (System Admin only)"""
        try:
            if not self.check_admin_permission(admin_role):
                return {
                    "success": False,
                    "error": "Access denied: System Administrator role required",
                    "required_role": "SYSTEM_ADMIN"
                }
            
            # Find user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "success": False,
                    "error": f"User with ID {user_id} not found"
                }
            
            # Update fields
            if user_data.full_name is not None:
                user.full_name = user_data.full_name
            if user_data.department is not None:
                user.department = user_data.department
            if user_data.role is not None:
                user.role = user_data.role
            if user_data.is_active is not None:
                user.is_active = user_data.is_active
            
            user.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(user)
            
            self.logger.info(f"User updated successfully: {user.email}")
            
            return {
                "success": True,
                "message": "User updated successfully",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "role": user.role.value,
                    "department": user.department,
                    "employee_id": user.employee_id,
                    "is_active": user.is_active,
                    "updated_at": user.updated_at.isoformat()
                }
            }
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error updating user: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to update user: {str(e)}"
            }
    
    def reset_password(self, admin_role: str, user_id: int, new_password: str, db: Session) -> Dict[str, Any]:
        """Reset user password (System Admin only)"""
        try:
            if not self.check_admin_permission(admin_role):
                return {
                    "success": False,
                    "error": "Access denied: System Administrator role required",
                    "required_role": "SYSTEM_ADMIN"
                }
            
            # Find user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "success": False,
                    "error": f"User with ID {user_id} not found"
                }
            
            # Hash new password
            user.hashed_password = pwd_context.hash(new_password)
            user.updated_at = datetime.utcnow()
            
            db.commit()
            
            self.logger.info(f"Password reset for user: {user.email}")
            
            return {
                "success": True,
                "message": "Password reset successfully",
                "user_email": user.email
            }
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error resetting password: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to reset password: {str(e)}"
            }
    
    def get_system_stats(self, admin_role: str, db: Session) -> Dict[str, Any]:
        """Get system statistics (System Admin only)"""
        try:
            if not self.check_admin_permission(admin_role):
                return {
                    "success": False,
                    "error": "Access denied: System Administrator role required",
                    "required_role": "SYSTEM_ADMIN"
                }
            
            # Get user statistics
            total_users = db.query(User).count()
            active_users = db.query(User).filter(User.is_active == True).count()
            inactive_users = total_users - active_users
            
            # Get role distribution
            role_stats = {}
            for role in UserRole:
                count = db.query(User).filter(User.role == role).count()
                role_stats[role.value] = count
            
            # Get department distribution
            dept_stats = {}
            departments = db.query(User.department).distinct().all()
            for dept in departments:
                if dept[0]:  # Skip None departments
                    count = db.query(User).filter(User.department == dept[0]).count()
                    dept_stats[dept[0]] = count
            
            return {
                "success": True,
                "system_stats": {
                    "total_users": total_users,
                    "active_users": active_users,
                    "inactive_users": inactive_users,
                    "role_distribution": role_stats,
                    "department_distribution": dept_stats,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system stats: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to get system stats: {str(e)}"
            }

# Create global instance
user_management_service = UserManagementService()
