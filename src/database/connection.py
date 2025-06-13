"""
Database Connection and Session Management for FinSolve RBAC Chatbot
Production-grade database setup with connection pooling, health checks,
and comprehensive error handling.

Author: Peter Pandey
Version: 1.0.0
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator, Optional
import time
from loguru import logger

from ..core.config import settings


class DatabaseManager:
    """
    Database manager with connection pooling, health checks,
    and automatic retry logic
    """
    
    def __init__(self):
        self.database_url = settings.database_url
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
        
    def _initialize_engine(self):
        """Initialize database engine with appropriate configuration"""
        
        # Engine configuration based on database type
        if self.database_url.startswith("sqlite"):
            # SQLite configuration
            self.engine = create_engine(
                self.database_url,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 20
                },
                poolclass=StaticPool,
                echo=settings.debug,
                future=True
            )
        else:
            # PostgreSQL/MySQL configuration
            self.engine = create_engine(
                self.database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=settings.debug,
                future=True
            )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Add event listeners
        self._setup_event_listeners()
        
        logger.info(f"Database engine initialized: {self.database_url}")
    
    def _setup_event_listeners(self):
        """Setup database event listeners for monitoring and optimization"""
        
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite pragmas for better performance and reliability"""
            if self.database_url.startswith("sqlite"):
                cursor = dbapi_connection.cursor()
                # Enable foreign key constraints
                cursor.execute("PRAGMA foreign_keys=ON")
                # Set journal mode to WAL for better concurrency
                cursor.execute("PRAGMA journal_mode=WAL")
                # Set synchronous mode to NORMAL for better performance
                cursor.execute("PRAGMA synchronous=NORMAL")
                # Set cache size (negative value means KB)
                cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
                cursor.close()
        
        @event.listens_for(self.engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Log slow queries for performance monitoring"""
            context._query_start_time = time.time()
        
        @event.listens_for(self.engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Log query execution time"""
            total = time.time() - context._query_start_time
            if total > 1.0:  # Log queries taking more than 1 second
                logger.warning(f"Slow query detected: {total:.2f}s - {statement[:100]}...")
    
    def create_tables(self):
        """Create all database tables"""
        from ..auth.models import Base
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        from ..auth.models import Base
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("All database tables dropped")
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    @contextmanager
    def get_session_context(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """Perform database health check"""
        try:
            with self.get_session_context() as session:
                # Simple query to test connection
                result = session.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    def get_connection_info(self) -> dict:
        """Get database connection information"""
        try:
            with self.get_session_context() as session:
                if self.database_url.startswith("sqlite"):
                    # SQLite specific info
                    result = session.execute(text("PRAGMA database_list")).fetchall()
                    return {
                        "type": "SQLite",
                        "databases": [dict(row._mapping) for row in result],
                        "url": self.database_url
                    }
                else:
                    # PostgreSQL/MySQL info
                    result = session.execute(text("SELECT version()")).scalar()
                    return {
                        "type": "PostgreSQL/MySQL",
                        "version": result,
                        "url": self.database_url.split("@")[-1] if "@" in self.database_url else self.database_url
                    }
        except Exception as e:
            logger.error(f"Failed to get connection info: {str(e)}")
            return {"error": str(e)}
    
    def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")


# Global database manager instance
db_manager = DatabaseManager()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database session
    """
    session = db_manager.get_session()
    try:
        yield session
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error in dependency: {str(e)}")
        raise
    finally:
        session.close()


def init_database():
    """Initialize database with tables and default data"""
    try:
        # Create tables
        db_manager.create_tables()
        
        # Create default users if they don't exist
        create_default_users()
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


def create_default_users():
    """Create default users for testing and demonstration"""
    from ..auth.service import auth_service
    from ..auth.models import UserCreate
    from ..core.config import UserRole
    
    default_users = [
        {
            "username": "admin",
            "email": "admin@finsolve.com",
            "full_name": "System Administrator",
            "password": "Admin123!",
            "role": UserRole.SYSTEM_ADMIN,
            "department": "IT",
            "employee_id": "ADMIN001"
        },
        {
            "username": "ceo.finsolve",
            "email": "ceo@finsolve.com",
            "full_name": "Chief Executive Officer",
            "password": "CEO123!",
            "role": UserRole.CEO,
            "department": "Executive",
            "employee_id": "CEO001"
        },
        {
            "username": "cfo.finsolve",
            "email": "cfo@finsolve.com",
            "full_name": "Chief Financial Officer",
            "password": "CFO123!",
            "role": UserRole.CFO,
            "department": "Finance",
            "employee_id": "CFO001"
        },
        {
            "username": "cto.finsolve",
            "email": "cto@finsolve.com",
            "full_name": "Chief Technology Officer",
            "password": "CTO123!",
            "role": UserRole.CTO,
            "department": "Engineering",
            "employee_id": "CTO001"
        },
        {
            "username": "chro.finsolve",
            "email": "chro@finsolve.com",
            "full_name": "Chief Human Resources Officer",
            "password": "CHRO123!",
            "role": UserRole.CHRO,
            "department": "Human Resources",
            "employee_id": "CHRO001"
        },
        {
            "username": "vp.marketing",
            "email": "vp.marketing@finsolve.com",
            "full_name": "VP Marketing",
            "password": "Marketing123!",
            "role": UserRole.VP_MARKETING,
            "department": "Marketing",
            "employee_id": "VPMKT001"
        },
        {
            "username": "john.doe",
            "email": "john.doe@finsolve.com",
            "full_name": "John Doe",
            "password": "Employee123!",
            "role": UserRole.EMPLOYEE,
            "department": "General",
            "employee_id": "EMP001"
        },
        {
            "username": "jane.smith",
            "email": "jane.smith@finsolve.com",
            "full_name": "Jane Smith",
            "password": "HRpass123!",
            "role": UserRole.HR,
            "department": "Human Resources",
            "employee_id": "HR001"
        },
        {
            "username": "mike.johnson",
            "email": "mike.johnson@finsolve.com",
            "full_name": "Mike Johnson",
            "password": "Finance123!",
            "role": UserRole.FINANCE,
            "department": "Finance",
            "employee_id": "FIN001"
        },
        {
            "username": "sarah.wilson",
            "email": "sarah.wilson@finsolve.com",
            "full_name": "Sarah Wilson",
            "password": "Marketing123!",
            "role": UserRole.MARKETING,
            "department": "Marketing",
            "employee_id": "MKT001"
        },
        {
            "username": "peter.pandey",
            "email": "peter.pandey@finsolve.com",
            "full_name": "Peter Pandey",
            "password": "Engineering123!",
            "role": UserRole.ENGINEERING,
            "department": "Engineering",
            "employee_id": "ENG001"
        }
    ]
    
    with db_manager.get_session_context() as session:
        for user_data in default_users:
            # Check if user already exists
            existing_user = auth_service.get_user_by_username(session, user_data["username"])
            if not existing_user:
                try:
                    user_create = UserCreate(**user_data)
                    auth_service.create_user(session, user_create)
                    logger.info(f"Created default user: {user_data['username']}")
                except Exception as e:
                    logger.warning(f"Failed to create default user {user_data['username']}: {str(e)}")


# Export commonly used functions and objects
__all__ = [
    "db_manager",
    "get_db",
    "init_database",
    "create_default_users"
]
