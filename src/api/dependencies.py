"""
API Dependencies for FinSolve RBAC Chatbot
Dependency injection for authentication, database sessions, and role-based access control.

Author: Peter Pandey
Version: 1.0.0
"""

from typing import Optional, Generator
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from loguru import logger

from ..database.connection import get_db
from ..auth.service import auth_service, AuthenticationError
from ..auth.models import User, TokenData
from ..core.config import UserRole, ROLE_PERMISSIONS


# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token
        token_data = auth_service.verify_token(credentials.credentials)
        
        if token_data.user_id is None:
            raise credentials_exception
        
        # Get user from database
        user = auth_service.get_user_by_id(db, user_id=token_data.user_id)
        
        if user is None:
            raise credentials_exception
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user"
            )
        
        # Verify session is still active
        if token_data.session_id:
            session = auth_service.get_active_session(db, token_data.session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session expired or invalid"
                )
        
        return user
        
    except AuthenticationError:
        raise credentials_exception
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user is active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_role(required_role: UserRole):
    """
    Dependency factory to require specific user role
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != required_role and current_user.role != UserRole.C_LEVEL:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role.value}"
            )
        return current_user
    
    return role_checker


def require_roles(required_roles: list[UserRole]):
    """
    Dependency factory to require one of multiple roles
    """
    def roles_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in required_roles and current_user.role != UserRole.C_LEVEL:
            role_names = [role.value for role in required_roles]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(role_names)}"
            )
        return current_user
    
    return roles_checker


def require_department_access(department: str):
    """
    Dependency factory to require access to specific department data
    """
    def department_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not ROLE_PERMISSIONS.can_access_department(current_user.role, department):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to {department} department data"
            )
        return current_user
    
    return department_checker


async def get_optional_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to get user if authenticated, None otherwise
    Useful for endpoints that work with or without authentication
    """
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        token_data = auth_service.verify_token(token)
        
        if token_data.user_id is None:
            return None
        
        user = auth_service.get_user_by_id(db, user_id=token_data.user_id)
        
        if user and user.is_active:
            return user
        
        return None
        
    except Exception:
        return None


class RoleBasedAccess:
    """
    Class-based dependency for complex role-based access control
    """
    
    def __init__(
        self,
        allowed_roles: Optional[list[UserRole]] = None,
        allowed_departments: Optional[list[str]] = None,
        require_own_data: bool = False
    ):
        self.allowed_roles = allowed_roles or []
        self.allowed_departments = allowed_departments or []
        self.require_own_data = require_own_data
    
    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        # C-level always has access
        if current_user.role == UserRole.C_LEVEL:
            return current_user
        
        # Check role access
        if self.allowed_roles and current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role permissions"
            )
        
        # Check department access
        if self.allowed_departments and current_user.department not in self.allowed_departments:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Department access denied"
            )
        
        return current_user


def validate_session_access(session_id: str):
    """
    Dependency factory to validate session access
    """
    def session_validator(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        # Get session
        session = auth_service.get_active_session(db, session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or expired"
            )
        
        # Check if user owns the session or has admin privileges
        if session.user_id != current_user.id and current_user.role != UserRole.C_LEVEL:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session"
            )
        
        return current_user
    
    return session_validator


async def get_request_context(request: Request) -> dict:
    """
    Dependency to get request context information
    """
    return {
        "request_id": getattr(request.state, "request_id", "unknown"),
        "client_ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
        "method": request.method,
        "path": request.url.path,
        "timestamp": request.state.start_time if hasattr(request.state, "start_time") else None
    }


class DataAccessValidator:
    """
    Validator for data access based on user role and data sensitivity
    """
    
    @staticmethod
    def validate_employee_data_access(
        user: User,
        target_employee_id: Optional[str] = None
    ) -> bool:
        """Validate access to employee data"""
        
        # C-level and HR have full access
        if user.role in [UserRole.C_LEVEL, UserRole.HR]:
            return True
        
        # Users can access their own data
        if target_employee_id and user.employee_id == target_employee_id:
            return True
        
        # Other roles have limited access
        return False
    
    @staticmethod
    def validate_financial_data_access(user: User) -> bool:
        """Validate access to financial data"""
        return user.role in [UserRole.C_LEVEL, UserRole.FINANCE]
    
    @staticmethod
    def validate_marketing_data_access(user: User) -> bool:
        """Validate access to marketing data"""
        return user.role in [UserRole.C_LEVEL, UserRole.MARKETING]
    
    @staticmethod
    def validate_engineering_data_access(user: User) -> bool:
        """Validate access to engineering data"""
        return user.role in [UserRole.C_LEVEL, UserRole.ENGINEERING]


def require_data_access(data_type: str):
    """
    Dependency factory for data type access validation
    """
    def access_validator(current_user: User = Depends(get_current_active_user)) -> User:
        validator = DataAccessValidator()
        
        access_granted = False
        
        if data_type == "employee":
            access_granted = validator.validate_employee_data_access(current_user)
        elif data_type == "financial":
            access_granted = validator.validate_financial_data_access(current_user)
        elif data_type == "marketing":
            access_granted = validator.validate_marketing_data_access(current_user)
        elif data_type == "engineering":
            access_granted = validator.validate_engineering_data_access(current_user)
        else:
            # General data access - all authenticated users
            access_granted = True
        
        if not access_granted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to {data_type} data"
            )
        
        return current_user
    
    return access_validator


# Common dependency combinations
require_hr_access = require_role(UserRole.HR)
require_finance_access = require_role(UserRole.FINANCE)
require_marketing_access = require_role(UserRole.MARKETING)
require_engineering_access = require_role(UserRole.ENGINEERING)
require_admin_access = require_role(UserRole.C_LEVEL)

require_hr_or_admin = require_roles([UserRole.HR, UserRole.C_LEVEL])
require_finance_or_admin = require_roles([UserRole.FINANCE, UserRole.C_LEVEL])
require_marketing_or_admin = require_roles([UserRole.MARKETING, UserRole.C_LEVEL])
require_engineering_or_admin = require_roles([UserRole.ENGINEERING, UserRole.C_LEVEL])
