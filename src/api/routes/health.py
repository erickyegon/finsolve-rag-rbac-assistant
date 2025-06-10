"""
Health Check Routes for FinSolve RBAC Chatbot API
Comprehensive health monitoring endpoints for system status, dependencies, and metrics.

Author: Peter Pandey
Version: 1.0.0
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import time
import psutil
import os
from datetime import datetime

from ...database.connection import get_db, db_manager
from ...rag.vector_store import vector_store
from ...core.config import settings
from ..middleware import metrics_middleware

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint
    Returns simple status for load balancers and monitoring
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": settings.app_name,
        "version": settings.app_version
    }


@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Detailed health check with dependency status
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "service": {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment
        },
        "dependencies": {},
        "system": {},
        "uptime": time.time()  # Will be calculated properly in production
    }
    
    # Check database health
    try:
        db_healthy = db_manager.health_check()
        health_status["dependencies"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "connection_info": db_manager.get_connection_info(),
            "response_time": "< 100ms"  # Placeholder
        }
    except Exception as e:
        health_status["dependencies"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check vector store health
    try:
        vector_stats = vector_store.get_collection_stats()
        health_status["dependencies"]["vector_store"] = {
            "status": "healthy" if vector_stats else "unhealthy",
            "stats": vector_stats
        }
    except Exception as e:
        health_status["dependencies"]["vector_store"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # System metrics
    try:
        health_status["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else "N/A"
        }
    except Exception as e:
        health_status["system"] = {"error": str(e)}
    
    return health_status


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Get application metrics
    """
    try:
        return metrics_middleware.get_metrics()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metrics: {str(e)}"
        )


@router.get("/database")
async def database_health(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Detailed database health check
    """
    try:
        start_time = time.time()
        
        # Test basic connectivity
        db_healthy = db_manager.health_check()
        
        # Get connection info
        connection_info = db_manager.get_connection_info()
        
        response_time = time.time() - start_time
        
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "response_time": f"{response_time:.3f}s",
            "connection_info": connection_info,
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }


@router.get("/vector-store")
async def vector_store_health() -> Dict[str, Any]:
    """
    Vector store health check
    """
    try:
        start_time = time.time()
        
        # Get collection stats
        stats = vector_store.get_collection_stats()
        
        response_time = time.time() - start_time
        
        return {
            "status": "healthy" if stats else "unhealthy",
            "response_time": f"{response_time:.3f}s",
            "stats": stats,
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }


@router.get("/system")
async def system_health() -> Dict[str, Any]:
    """
    System resource health check
    """
    try:
        # CPU information
        cpu_info = {
            "percent": psutil.cpu_percent(interval=1),
            "count": psutil.cpu_count(),
            "count_logical": psutil.cpu_count(logical=True)
        }
        
        # Memory information
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
            "free": memory.free
        }
        
        # Disk information
        disk = psutil.disk_usage('/')
        disk_info = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": (disk.used / disk.total) * 100
        }
        
        # Network information
        network = psutil.net_io_counters()
        network_info = {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv
        }
        
        # Process information
        process = psutil.Process()
        process_info = {
            "pid": process.pid,
            "memory_percent": process.memory_percent(),
            "cpu_percent": process.cpu_percent(),
            "num_threads": process.num_threads(),
            "create_time": process.create_time()
        }
        
        return {
            "status": "healthy",
            "cpu": cpu_info,
            "memory": memory_info,
            "disk": disk_info,
            "network": network_info,
            "process": process_info,
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }


@router.get("/readiness")
async def readiness_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Kubernetes readiness probe endpoint
    Checks if the application is ready to serve traffic
    """
    checks = {
        "database": False,
        "vector_store": False
    }
    
    # Check database
    try:
        checks["database"] = db_manager.health_check()
    except Exception:
        pass
    
    # Check vector store
    try:
        stats = vector_store.get_collection_stats()
        checks["vector_store"] = bool(stats)
    except Exception:
        pass
    
    all_healthy = all(checks.values())
    
    return {
        "ready": all_healthy,
        "checks": checks,
        "timestamp": time.time()
    }


@router.get("/liveness")
async def liveness_check() -> Dict[str, Any]:
    """
    Kubernetes liveness probe endpoint
    Checks if the application is alive and should not be restarted
    """
    return {
        "alive": True,
        "timestamp": time.time(),
        "service": settings.app_name
    }
