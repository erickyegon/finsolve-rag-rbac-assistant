"""
Authentication Models for FinSolve RBAC Chatbot
Database models for user management, authentication, and role-based access control.

Author: Peter Pandey
Version: 1.0.0
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr, field_validator
from enum import Enum
import uuid

from ..core.config import UserRole

Base = declarative_base()


class User(Base):
    """
    User model for authentication and role management
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.EMPLOYEE)
    department = Column(String(100), nullable=True)
    employee_id = Column(String(50), unique=True, index=True, nullable=True)
    
    # Status and metadata
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    chat_history = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(email='{self.email}', role='{self.role}', department='{self.department}')>"


class UserSession(Base):
    """
    User session model for tracking active sessions
    """
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    last_accessed = Column(DateTime, default=func.now())
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<UserSession(user_id={self.user_id}, expires_at='{self.expires_at}')>"


class ChatHistory(Base):
    """
    Chat history model for storing conversation data
    """
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_type = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    message_metadata = Column(Text, nullable=True)  # JSON string for additional data
    timestamp = Column(DateTime, default=func.now())
    
    # RAG-specific fields
    retrieved_documents = Column(Text, nullable=True)  # JSON string
    confidence_score = Column(String(10), nullable=True)
    processing_time = Column(String(10), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="chat_history")
    
    def __repr__(self):
        return f"<ChatHistory(user_id={self.user_id}, type='{self.message_type}', timestamp='{self.timestamp}')>"


# Pydantic models for API requests/responses

class UserBase(BaseModel):
    """Base user model for shared attributes"""
    email: EmailStr
    username: str
    full_name: str
    role: UserRole
    department: Optional[str] = None
    employee_id: Optional[str] = None


class UserCreate(UserBase):
    """User creation model"""
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        import re
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError('Username must contain only alphanumeric characters, dots, underscores, or hyphens')
        return v


class UserRegistration(BaseModel):
    """Public user registration model for new employees"""
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    department: str
    role: str  # Will be mapped to UserRole
    job_title: str
    employee_id: Optional[str] = None
    manager_email: Optional[str] = None
    access_reason: str

    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_names(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        return v.strip()

    @field_validator('department')
    @classmethod
    def validate_department(cls, v):
        valid_departments = [
            "Engineering", "Finance", "HR", "Marketing", "Sales",
            "Customer Support", "IT Security", "Data Analytics",
            "R&D", "QA", "Operations", "Legal", "Executive"
        ]
        if v not in valid_departments:
            raise ValueError(f'Department must be one of: {", ".join(valid_departments)}')
        return v

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        valid_roles = ["Employee", "Manager", "Director", "C-Level Executive"]
        if v not in valid_roles:
            raise ValueError(f'Role must be one of: {", ".join(valid_roles)}')
        return v

    @field_validator('access_reason')
    @classmethod
    def validate_access_reason(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Access reason must be at least 10 characters long')
        return v.strip()


class RegistrationResponse(BaseModel):
    """Registration response model"""
    message: str
    user_id: int
    email: str
    temporary_password: str
    status: str = "pending_activation"


class UserUpdate(BaseModel):
    """User update model"""
    full_name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response model"""
    id: int
    uuid: str
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """User login model"""
    username: str
    password: str


class Token(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenData(BaseModel):
    """Token data model for JWT payload"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[UserRole] = None
    session_id: Optional[str] = None


class ChatMessage(BaseModel):
    """Chat message model"""
    content: str
    message_type: str = "user"
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model"""
    content: str
    message_type: str = "assistant"
    session_id: str
    retrieved_documents: Optional[List[str]] = None
    confidence_score: Optional[float] = None
    processing_time: Optional[float] = None
    timestamp: datetime
    visualization: Optional[Dict[str, Any]] = None


class SessionInfo(BaseModel):
    """Session information model"""
    session_id: str
    user: UserResponse
    expires_at: datetime
    last_accessed: datetime
    ip_address: Optional[str] = None
    
    class Config:
        from_attributes = True
