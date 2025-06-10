"""
Authentication Routes for FinSolve RBAC Chatbot API
Comprehensive authentication endpoints including login, logout, registration,
token refresh, and session management.

Author: Dr. Erick K. Yegon
Email: keyegon@gmail.com
Version: 1.0.0
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import time
import secrets
import string
from loguru import logger

from ...database.connection import get_db
from ...auth.service import auth_service, AuthenticationError
from ...auth.models import (
    UserCreate, UserLogin, UserResponse, Token,
    SessionInfo, User, UserUpdate, UserRegistration, RegistrationResponse
)
from ...core.config import UserRole
from ..dependencies import (
    get_current_user, get_current_active_user, 
    require_admin_access, security
)

router = APIRouter()


@router.post("/register-employee", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_new_employee(
    registration_data: UserRegistration,
    db: Session = Depends(get_db)
) -> RegistrationResponse:
    """
    Public registration endpoint for new employees
    Creates a new user account with temporary password and sends welcome email
    """
    try:
        # Generate temporary password
        temp_password = generate_temporary_password()

        # Map role string to UserRole enum
        role_mapping = {
            "Employee": UserRole.EMPLOYEE,
            "Manager": UserRole.MANAGER,
            "Director": UserRole.DIRECTOR,
            "C-Level Executive": UserRole.C_LEVEL
        }

        user_role = role_mapping.get(registration_data.role, UserRole.EMPLOYEE)

        # Create username from email
        username = registration_data.email.split('@')[0]

        # Create UserCreate object
        user_create = UserCreate(
            email=registration_data.email,
            username=username,
            full_name=f"{registration_data.first_name} {registration_data.last_name}",
            password=temp_password,
            role=user_role,
            department=registration_data.department,
            employee_id=registration_data.employee_id
        )

        # Check if user already exists
        existing_user = auth_service.get_user_by_email(db, registration_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )

        # Create user (initially inactive for approval)
        new_user = auth_service.create_user(db, user_create)
        new_user.is_active = False  # Require activation
        db.commit()

        # Store additional registration data (you might want to create a separate table for this)
        # For now, we'll log it
        logger.info(f"New employee registration: {registration_data.email}, "
                   f"Department: {registration_data.department}, "
                   f"Job Title: {registration_data.job_title}, "
                   f"Manager: {registration_data.manager_email}, "
                   f"Reason: {registration_data.access_reason}")

        logger.info(f"New employee registered: {new_user.email} (ID: {new_user.id})")

        return RegistrationResponse(
            message="Registration successful! Check your email for login credentials.",
            user_id=new_user.id,
            email=new_user.email,
            temporary_password=temp_password,
            status="pending_activation"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Employee registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


def generate_temporary_password(length: int = 12) -> str:
    """Generate a secure temporary password"""
    # Ensure we have at least one of each character type
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = "!@#$%^&*"

    # Start with one of each required type
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special)
    ]

    # Fill the rest with random choices from all types
    all_chars = lowercase + uppercase + digits + special
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))

    # Shuffle the password list
    secrets.SystemRandom().shuffle(password)

    return ''.join(password)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_access)  # Only admins can create users
) -> UserResponse:
    """
    Register a new user (Admin only)
    """
    try:
        # Create user
        new_user = auth_service.create_user(db, user_data)
        
        logger.info(f"New user registered: {new_user.username} by admin: {current_user.username}")
        
        return UserResponse.from_orm(new_user)
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"User registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
) -> Token:
    """
    Authenticate user and return access token
    """
    try:
        # Authenticate user
        user = auth_service.authenticate_user(
            db, 
            user_credentials.username, 
            user_credentials.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Create session
        session_data = auth_service.create_user_session(
            db, user, client_ip, user_agent
        )
        
        logger.info(f"User logged in: {user.username} from {client_ip}")
        
        return Token(
            access_token=session_data["access_token"],
            refresh_token=session_data["refresh_token"],
            token_type="bearer",
            expires_in=session_data["expires_in"],
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Logout user and invalidate session
    """
    try:
        # Verify token to get session ID
        token_data = auth_service.verify_token(credentials.credentials)
        
        if token_data.session_id:
            # Invalidate session
            success = auth_service.invalidate_session(db, token_data.session_id)
            
            if success:
                logger.info(f"User logged out: {token_data.username}")
                return {"message": "Successfully logged out"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Logout failed"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session"
            )
            
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: Dict[str, str],
    db: Session = Depends(get_db)
) -> Token:
    """
    Refresh access token using refresh token
    """
    try:
        refresh_token = refresh_data.get("refresh_token")
        session_id = refresh_data.get("session_id")
        
        if not refresh_token or not session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token and session ID required"
            )
        
        # Refresh token
        new_tokens = auth_service.refresh_access_token(db, refresh_token, session_id)
        
        if not new_tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user for response
        session = auth_service.get_active_session(db, session_id)
        user = session.user if session else None
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session"
            )
        
        logger.info(f"Token refreshed for user: {user.username}")
        
        return Token(
            access_token=new_tokens["access_token"],
            refresh_token=new_tokens["refresh_token"],
            token_type="bearer",
            expires_in=new_tokens["expires_in"],
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """
    Get current user information
    """
    return UserResponse.from_orm(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Update current user information
    """
    try:
        # Update allowed fields
        if user_update.full_name is not None:
            current_user.full_name = user_update.full_name
        
        if user_update.department is not None:
            current_user.department = user_update.department
        
        # Only admins can change roles and active status
        if current_user.role == UserRole.C_LEVEL:
            if user_update.role is not None:
                current_user.role = user_update.role
            
            if user_update.is_active is not None:
                current_user.is_active = user_update.is_active
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"User updated: {current_user.username}")
        
        return UserResponse.from_orm(current_user)
        
    except Exception as e:
        db.rollback()
        logger.error(f"User update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User update failed"
        )


@router.get("/sessions", response_model=List[SessionInfo])
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[SessionInfo]:
    """
    Get current user's active sessions
    """
    try:
        sessions = db.query(auth_service.UserSession).filter(
            auth_service.UserSession.user_id == current_user.id,
            auth_service.UserSession.is_active == True
        ).all()
        
        return [SessionInfo.from_orm(session) for session in sessions]
        
    except Exception as e:
        logger.error(f"Failed to get user sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )


@router.delete("/sessions/{session_id}")
async def invalidate_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Invalidate a specific session
    """
    try:
        # Get session
        session = auth_service.get_active_session(db, session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Check if user owns the session or is admin
        if session.user_id != current_user.id and current_user.role != UserRole.C_LEVEL:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Invalidate session
        success = auth_service.invalidate_session(db, session_id)
        
        if success:
            logger.info(f"Session invalidated: {session_id} by {current_user.username}")
            return {"message": "Session invalidated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to invalidate session"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session invalidation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session invalidation failed"
        )


@router.delete("/sessions")
async def invalidate_all_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Invalidate all user sessions (logout from all devices)
    """
    try:
        count = auth_service.invalidate_all_user_sessions(db, current_user.id)
        
        logger.info(f"All sessions invalidated for user: {current_user.username}")
        
        return {
            "message": "All sessions invalidated successfully",
            "invalidated_count": count
        }
        
    except Exception as e:
        logger.error(f"Failed to invalidate all sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invalidate sessions"
        )


@router.get("/permissions")
async def get_user_permissions(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get current user's permissions and access rights
    """
    permissions = auth_service.get_user_permissions(current_user.role)
    
    return {
        "user": {
            "username": current_user.username,
            "role": current_user.role.value,
            "department": current_user.department
        },
        "permissions": permissions,
        "timestamp": time.time()
    }


@router.post("/validate-token")
async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Validate token and return user information
    """
    try:
        # Verify token
        token_data = auth_service.verify_token(credentials.credentials)
        
        # Get user
        user = auth_service.get_user_by_id(db, token_data.user_id)
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or inactive user"
            )
        
        return {
            "valid": True,
            "user": UserResponse.from_orm(user).dict(),
            "token_data": {
                "user_id": token_data.user_id,
                "username": token_data.username,
                "role": token_data.role.value if token_data.role else None,
                "session_id": token_data.session_id
            },
            "timestamp": time.time()
        }
        
    except AuthenticationError:
        return {
            "valid": False,
            "error": "Invalid token",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Token validation failed: {str(e)}")
        return {
            "valid": False,
            "error": "Validation failed",
            "timestamp": time.time()
        }
