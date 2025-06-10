"""
Authentication Service for FinSolve RBAC Chatbot
Comprehensive authentication, authorization, and session management.

Author: Peter Pandey
Version: 1.0.0
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from passlib.context import CryptContext
from jose import JWTError, jwt
import uuid
import secrets
from loguru import logger

from .models import User, UserSession, UserCreate, UserLogin, TokenData
from ..core.config import settings, UserRole, ROLE_PERMISSIONS
from ..database.connection import get_db


class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass


class AuthorizationError(Exception):
    """Custom exception for authorization errors"""
    pass


class AuthService:
    """
    Comprehensive authentication service with:
    - Password hashing and verification
    - JWT token generation and validation
    - Session management
    - Role-based access control
    - Security logging and monitoring
    """
    
    def __init__(self):
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=settings.bcrypt_rounds
        )
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        
        logger.info("Authentication service initialized")
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self) -> str:
        """Create a secure refresh token"""
        return secrets.token_urlsafe(32)
    
    def verify_token(self, token: str) -> TokenData:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: int = payload.get("user_id")
            username: str = payload.get("username")
            role: str = payload.get("role")
            session_id: str = payload.get("session_id")
            
            if user_id is None or username is None:
                raise AuthenticationError("Invalid token payload")
            
            return TokenData(
                user_id=user_id,
                username=username,
                role=UserRole(role) if role else None,
                session_id=session_id
            )
        except JWTError as e:
            logger.warning(f"JWT verification failed: {str(e)}")
            raise AuthenticationError("Could not validate credentials")
    
    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    def create_user(self, db: Session, user_create: UserCreate) -> User:
        """Create a new user"""
        # Check if user already exists
        if self.get_user_by_username(db, user_create.username):
            raise AuthenticationError("Username already registered")
        
        if self.get_user_by_email(db, user_create.email):
            raise AuthenticationError("Email already registered")
        
        # Create new user
        hashed_password = self.hash_password(user_create.password)
        
        db_user = User(
            email=user_create.email,
            username=user_create.username,
            full_name=user_create.full_name,
            hashed_password=hashed_password,
            role=user_create.role,
            department=user_create.department,
            employee_id=user_create.employee_id,
            uuid=str(uuid.uuid4())
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"New user created: {user_create.username} ({user_create.email})")
        return db_user
    
    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password"""
        user = self.get_user_by_username(db, username)
        
        if not user:
            logger.warning(f"Authentication failed: user not found - {username}")
            return None
        
        if not user.is_active:
            logger.warning(f"Authentication failed: user inactive - {username}")
            return None
        
        if not self.verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: invalid password - {username}")
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        logger.info(f"User authenticated successfully: {username}")
        return user
    
    def create_user_session(
        self,
        db: Session,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new user session with tokens"""
        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        # Create token payload
        token_data = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role.value,
            "session_id": session_id
        }
        
        # Generate tokens
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token()
        
        # Create session record
        session = UserSession(
            session_id=session_id,
            user_id=user.id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info(f"Session created for user: {user.username} (session: {session_id})")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60,
            "session_id": session_id,
            "user": user
        }
    
    def get_active_session(self, db: Session, session_id: str) -> Optional[UserSession]:
        """Get active session by session ID"""
        return db.query(UserSession).filter(
            and_(
                UserSession.session_id == session_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        ).first()
    
    def invalidate_session(self, db: Session, session_id: str) -> bool:
        """Invalidate a user session"""
        session = db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()
        
        if session:
            session.is_active = False
            db.commit()
            logger.info(f"Session invalidated: {session_id}")
            return True
        
        return False
    
    def invalidate_all_user_sessions(self, db: Session, user_id: int) -> int:
        """Invalidate all sessions for a user"""
        count = db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        ).update({"is_active": False})
        
        db.commit()
        logger.info(f"Invalidated {count} sessions for user ID: {user_id}")
        return count
    
    def refresh_access_token(
        self,
        db: Session,
        refresh_token: str,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Refresh an access token using refresh token"""
        session = db.query(UserSession).filter(
            and_(
                UserSession.session_id == session_id,
                UserSession.refresh_token == refresh_token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        ).first()
        
        if not session:
            logger.warning(f"Refresh token validation failed for session: {session_id}")
            return None
        
        user = session.user
        if not user or not user.is_active:
            logger.warning(f"User inactive during token refresh: {session_id}")
            return None
        
        # Create new tokens
        new_expires_at = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        token_data = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role.value,
            "session_id": session_id
        }
        
        new_access_token = self.create_access_token(token_data)
        new_refresh_token = self.create_refresh_token()
        
        # Update session
        session.access_token = new_access_token
        session.refresh_token = new_refresh_token
        session.expires_at = new_expires_at
        session.last_accessed = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Access token refreshed for user: {user.username}")
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60,
            "session_id": session_id
        }
    
    def check_permission(
        self,
        user_role: UserRole,
        department: str,
        data_type: str = None
    ) -> bool:
        """Check if user role has permission to access specific data"""
        return ROLE_PERMISSIONS.can_access_department(user_role, department)
    
    def get_user_permissions(self, user_role: UserRole) -> Dict[str, List[str]]:
        """Get all permissions for a user role"""
        return ROLE_PERMISSIONS.get_permissions(user_role)
    
    def cleanup_expired_sessions(self, db: Session) -> int:
        """Clean up expired sessions"""
        count = db.query(UserSession).filter(
            UserSession.expires_at < datetime.utcnow()
        ).delete()
        
        db.commit()
        logger.info(f"Cleaned up {count} expired sessions")
        return count


# Global auth service instance
auth_service = AuthService()
