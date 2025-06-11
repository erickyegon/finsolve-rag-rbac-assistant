"""
Configuration Management for FinSolve RBAC Chatbot
Centralized configuration with environment variable support,
validation, and type safety.

Author: Peter Pandey
Version: 1.0.0
"""

import os
from typing import List, Optional, Dict, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from enum import Enum
import json


class Environment(str, Enum):
    """Application environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class UserRole(str, Enum):
    """User roles with hierarchical access"""
    EMPLOYEE = "employee"
    HR = "hr"
    FINANCE = "finance"
    MARKETING = "marketing"
    ENGINEERING = "engineering"
    CEO = "ceo"  # Chief Executive Officer - highest business access
    SYSTEM_ADMIN = "system_admin"  # System Administrator - user management and system control


class Settings(BaseSettings):
    """
    Application settings with environment variable support
    and comprehensive validation
    """
    
    # Application Configuration
    app_name: str = Field(default="FinSolve Technologies AI Assistant", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: Environment = Field(default=Environment.DEVELOPMENT, env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    log_level: LogLevel = Field(default=LogLevel.INFO, env="LOG_LEVEL")
    
    # API Configuration
    euri_api_key: str = Field(..., env="EURI_API_KEY")
    euri_base_url: str = Field(
        default="https://api.euron.one/api/v1/euri/alpha/chat/completions",
        env="EURI_BASE_URL"
    )
    euri_timeout: int = Field(default=60, env="EURI_TIMEOUT")  # Increased timeout
    euri_max_retries: int = Field(default=2, env="EURI_MAX_RETRIES")  # Reduced retries
    euri_rate_limit: int = Field(default=30, env="EURI_RATE_LIMIT")  # More conservative rate limit

    # Euriai Embeddings Configuration
    euriai_api_key: Optional[str] = Field(default=None, env="EURIAI_API_KEY")
    euriai_embeddings_enabled: bool = Field(default=True, env="EURIAI_EMBEDDINGS_ENABLED")

    # OpenAI Fallback Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_timeout: int = Field(default=30, env="OPENAI_TIMEOUT")
    openai_max_tokens: int = Field(default=2000, env="OPENAI_MAX_TOKENS")
    
    # Security Configuration
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    bcrypt_rounds: int = Field(default=12, env="BCRYPT_ROUNDS")
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///./finsolve_rbac.db", env="DATABASE_URL")
    
    # Vector Database Configuration
    chroma_persist_directory: str = Field(default="./chroma_db", env="CHROMA_PERSIST_DIRECTORY")
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        env="EMBEDDING_MODEL"
    )
    vector_db_collection_name: str = Field(default="finsolve_documents", env="VECTOR_DB_COLLECTION")
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    
    # Server Configuration
    langserve_host: str = Field(default="0.0.0.0", env="LANGSERVE_HOST")
    langserve_port: int = Field(default=8000, env="LANGSERVE_PORT")
    streamlit_host: str = Field(default="0.0.0.0", env="STREAMLIT_HOST")
    streamlit_port: int = Field(default=8501, env="STREAMLIT_PORT")

    # Public URLs (for display purposes)
    @property
    def streamlit_url(self) -> str:
        """Get the public Streamlit URL"""
        return f"http://localhost:{self.streamlit_port}"

    @property
    def api_url(self) -> str:
        """Get the public API URL"""
        return f"http://localhost:{self.langserve_port}"

    @property
    def docs_url(self) -> str:
        """Get the API documentation URL"""
        return f"http://localhost:{self.langserve_port}/docs"

    @property
    def langserve_playground_url(self) -> str:
        """Get the LangServe playground URL"""
        return f"http://localhost:{self.langserve_port}/langserve/chat/playground"
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8501"],
        env="CORS_ORIGINS"
    )
    
    # Data Processing Configuration
    data_directory: str = Field(default="./data", env="DATA_DIRECTORY")
    max_file_size_mb: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    supported_file_types: List[str] = Field(
        default=[".md", ".txt", ".csv", ".json", ".pdf"],
        env="SUPPORTED_FILE_TYPES"
    )
    
    # RAG Configuration
    max_context_length: int = Field(default=4000, env="MAX_CONTEXT_LENGTH")
    similarity_threshold: float = Field(default=0.7, env="SIMILARITY_THRESHOLD")
    max_retrieved_docs: int = Field(default=5, env="MAX_RETRIEVED_DOCS")
    
    # LangGraph Configuration
    max_iterations: int = Field(default=10, env="MAX_ITERATIONS")
    recursion_limit: int = Field(default=50, env="RECURSION_LIMIT")
    
    # Monitoring and Observability
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    enable_tracing: bool = Field(default=True, env="ENABLE_TRACING")

    # Email Configuration
    system_email: str = Field(default="keyegon@gmail.com", env="SYSTEM_EMAIL")
    email_password: str = Field(default="", env="EMAIL_PASSWORD")
    smtp_server: str = Field(default="smtp.gmail.com", env="SMTP_SERVER")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    email_use_tls: bool = Field(default=True, env="EMAIL_USE_TLS")
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("supported_file_types", mode="before")
    @classmethod
    def parse_file_types(cls, v):
        """Parse supported file types from string or list"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [ft.strip() for ft in v.split(",")]
        return v
    
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v):
        """Validate secret key length"""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v
    
    @field_validator("similarity_threshold")
    @classmethod
    def validate_similarity_threshold(cls, v):
        """Validate similarity threshold range"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Similarity threshold must be between 0.0 and 1.0")
        return v
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }


class RolePermissions:
    """
    Role-based access control permissions mapping
    Defines what data each role can access
    """
    
    PERMISSIONS: Dict[UserRole, Dict[str, List[str]]] = {
        UserRole.EMPLOYEE: {
            "departments": ["general"],
            "data_types": ["policies", "handbook", "announcements", "faqs"],
            "restricted_fields": [],
            "can_access_personal_data": False
        },
        UserRole.HR: {
            "departments": ["hr", "general"],
            "data_types": ["employee_data", "policies", "handbook", "payroll", "performance"],
            "restricted_fields": ["salary"],  # Can see salary ranges but not individual salaries
            "can_access_personal_data": True
        },
        UserRole.FINANCE: {
            "departments": ["finance", "general"],
            "data_types": ["financial_reports", "expenses", "budgets", "vendor_costs", "policies"],
            "restricted_fields": [],
            "can_access_personal_data": False
        },
        UserRole.MARKETING: {
            "departments": ["marketing", "general"],
            "data_types": ["campaigns", "customer_data", "sales_metrics", "market_research", "policies"],
            "restricted_fields": [],
            "can_access_personal_data": False
        },
        UserRole.ENGINEERING: {
            "departments": ["engineering", "general"],
            "data_types": ["technical_docs", "architecture", "processes", "policies", "development"],
            "restricted_fields": [],
            "can_access_personal_data": False
        },
        UserRole.CEO: {
            "departments": ["finance", "marketing", "hr", "engineering", "general"],
            "data_types": ["all"],
            "restricted_fields": [],
            "can_access_personal_data": True,
            "can_view_all_data": True,
            "can_access_executive_reports": True,
            "can_view_financial_details": True,
            "can_access_strategic_data": True
        },
        UserRole.SYSTEM_ADMIN: {
            "departments": ["system", "general"],
            "data_types": ["user_management", "system_logs", "security_settings", "policies"],
            "restricted_fields": [],
            "can_access_personal_data": False,
            "can_manage_users": True,
            "can_access_system_settings": True,
            "can_view_audit_logs": True,
            "can_manage_roles": True,
            "can_reset_passwords": True,
            "can_access_business_data": False  # No access to business intelligence data
        }
    }
    
    @classmethod
    def get_permissions(cls, role: UserRole) -> Dict[str, List[str]]:
        """Get permissions for a specific role"""
        return cls.PERMISSIONS.get(role, cls.PERMISSIONS[UserRole.EMPLOYEE])
    
    @classmethod
    def can_access_department(cls, role: UserRole, department: str) -> bool:
        """Check if role can access specific department"""
        permissions = cls.get_permissions(role)
        return department.lower() in permissions["departments"]
    
    @classmethod
    def can_access_data_type(cls, role: UserRole, data_type: str) -> bool:
        """Check if role can access specific data type"""
        permissions = cls.get_permissions(role)
        return "all" in permissions["data_types"] or data_type.lower() in permissions["data_types"]
    
    @classmethod
    def get_restricted_fields(cls, role: UserRole) -> List[str]:
        """Get list of restricted fields for role"""
        permissions = cls.get_permissions(role)
        return permissions["restricted_fields"]


# Global settings instance
settings = Settings()

# Export commonly used configurations
ROLE_PERMISSIONS = RolePermissions()
USER_ROLES = UserRole
LOG_LEVELS = LogLevel
ENVIRONMENTS = Environment
