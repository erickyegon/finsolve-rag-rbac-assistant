"""
FastAPI Main Application for FinSolve RBAC Chatbot
Production-grade API server with LangServe integration, comprehensive middleware,
authentication, monitoring, and error handling.

Author: Peter Pandey
Version: 1.0.0
"""

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import uuid
from typing import Optional
from loguru import logger
import sys

# LangServe imports
from langserve import add_routes
from langchain_core.runnables import RunnableLambda

from ..core.config import settings
from ..database.connection import init_database, db_manager
from ..rag.vector_store import vector_store
from ..agents.graph import finsolve_agent
from .routes import auth, chat, admin, health
from .middleware import LoggingMiddleware, RateLimitMiddleware, SecurityMiddleware
from .dependencies import get_current_user, get_db


# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level
)
logger.add(
    "logs/finsolve_api.log",
    rotation="1 day",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=settings.log_level
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting FinSolve RBAC Chatbot API...")
    
    try:
        # Initialize database
        init_database()
        logger.info("Database initialized successfully")
        
        # Initialize vector store
        if not vector_store.get_collection_stats().get("total_documents", 0):
            logger.info("Indexing data sources...")
            vector_store.index_data_sources()
        
        logger.info("Application startup completed successfully")
        logger.info("=" * 50)
        logger.info("🚀 FinSolve Technologies AI Assistant API Ready!")
        logger.info(f"📊 API Server: {settings.api_url}")
        logger.info(f"📚 Documentation: {settings.docs_url}")
        logger.info(f"🔧 LangServe Playground: {settings.langserve_playground_url}")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down FinSolve RBAC Chatbot API...")
    db_manager.close()
    logger.info("Application shutdown completed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="FinSolve Technologies AI Assistant - Connected Intelligence through Advanced AI and Role-Based Security",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
    contact={
        "name": "Dr. Erick K. Yegon",
        "url": "https://finsolve.com",
        "email": "keyegon@gmail.com"
    },
    license_info={
        "name": "FinSolve Technologies License",
        "url": "https://finsolve.com/license"
    }
)

# Security
security = HTTPBearer()

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.finsolve.com"]
)

# Custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityMiddleware)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(f"Unhandled exception in request {request_id}: {str(exc)}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "request_id": request_id,
            "timestamp": time.time()
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP exception handler"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": request_id,
            "timestamp": time.time()
        }
    )


# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(admin.router, prefix="/admin", tags=["Administration"])


# LangServe integration
def create_chat_runnable():
    """Create a runnable for LangServe integration"""
    
    async def chat_endpoint(input_data: dict):
        """Chat endpoint for LangServe"""
        try:
            # Extract data
            query = input_data.get("query", "")
            user_data = input_data.get("user", {})
            session_id = input_data.get("session_id", str(uuid.uuid4()))
            
            # Create mock user object for processing
            class MockUser:
                def __init__(self, data):
                    self.id = data.get("id", 1)
                    self.username = data.get("username", "unknown")
                    self.role = data.get("role", "employee")
                    self.department = data.get("department", "general")
            
            user = MockUser(user_data)
            
            # Process query
            response = await finsolve_agent.process_query(query, user, session_id)
            
            return {
                "response": response.content,
                "sources": response.sources,
                "confidence_score": response.confidence_score,
                "processing_time": response.processing_time,
                "query_type": response.query_type.value,
                "metadata": response.metadata
            }
            
        except Exception as e:
            logger.error(f"LangServe chat endpoint error: {str(e)}")
            return {
                "response": f"Error processing request: {str(e)}",
                "sources": [],
                "confidence_score": 0.0,
                "processing_time": 0.0,
                "query_type": "error",
                "metadata": {"error": str(e)}
            }
    
    return RunnableLambda(chat_endpoint)


# Add LangServe routes
chat_runnable = create_chat_runnable()
add_routes(
    app,
    chat_runnable,
    path="/langserve/chat"
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "Production-grade RBAC chatbot for FinSolve Technologies",
        "status": "operational",
        "timestamp": time.time(),
        "endpoints": {
            "health": "/health",
            "auth": "/auth",
            "chat": "/chat",
            "admin": "/admin",
            "langserve": "/langserve/chat",
            "docs": "/docs" if settings.debug else "disabled",
            "redoc": "/redoc" if settings.debug else "disabled"
        }
    }


# API Information endpoint
@app.get("/info")
async def api_info():
    """Get detailed API information"""
    return {
        "application": {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "debug": settings.debug
        },
        "database": db_manager.get_connection_info(),
        "vector_store": vector_store.get_collection_stats(),
        "features": {
            "authentication": True,
            "role_based_access": True,
            "hybrid_mcp_rag": True,
            "langserve_integration": True,
            "real_time_chat": True,
            "document_search": True,
            "structured_data_query": True
        },
        "supported_roles": [role.value for role in settings.USER_ROLES],
        "timestamp": time.time()
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.langserve_host,
        port=settings.langserve_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
