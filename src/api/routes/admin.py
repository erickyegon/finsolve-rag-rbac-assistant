"""
Admin Routes for FinSolve RBAC Chatbot API
Administrative endpoints for user management, system monitoring,
data management, and system configuration.

Author: Peter Pandey
Version: 1.0.0
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import time
from datetime import datetime, timedelta
from loguru import logger

from ...database.connection import get_db, db_manager
from ...auth.models import User, UserCreate, UserResponse, UserUpdate, ChatHistory
from ...auth.service import auth_service
from ...rag.vector_store import vector_store
from ...data.processors import data_processor
from ...core.config import UserRole, settings
from ..dependencies import require_admin_access
from ..middleware import metrics_middleware

router = APIRouter()


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    role_filter: Optional[UserRole] = None,
    active_only: bool = True,
    current_user: User = Depends(require_admin_access),
    db: Session = Depends(get_db)
) -> List[UserResponse]:
    """
    Get all users with optional filtering
    """
    try:
        query = db.query(User)
        
        # Apply filters
        if role_filter:
            query = query.filter(User.role == role_filter)
        
        if active_only:
            query = query.filter(User.is_active == True)
        
        # Apply pagination
        users = query.offset(skip).limit(limit).all()
        
        return [UserResponse.from_orm(user) for user in users]
        
    except Exception as e:
        logger.error(f"Failed to get users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin_access),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Create a new user
    """
    try:
        new_user = auth_service.create_user(db, user_data)
        
        logger.info(f"User created by admin: {new_user.username} by {current_user.username}")
        
        return UserResponse.from_orm(new_user)
        
    except Exception as e:
        logger.error(f"User creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_admin_access),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Get specific user by ID
    """
    try:
        user = auth_service.get_user_by_id(db, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin_access),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Update user information
    """
    try:
        user = auth_service.get_user_by_id(db, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields
        if user_update.full_name is not None:
            user.full_name = user_update.full_name
        
        if user_update.department is not None:
            user.department = user_update.department
        
        if user_update.role is not None:
            user.role = user_update.role
        
        if user_update.is_active is not None:
            user.is_active = user_update.is_active
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"User updated by admin: {user.username} by {current_user.username}")
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"User update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User update failed"
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin_access),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Delete user (soft delete by deactivating)
    """
    try:
        user = auth_service.get_user_by_id(db, user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent self-deletion
        if user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        # Soft delete by deactivating
        user.is_active = False
        
        # Invalidate all user sessions
        auth_service.invalidate_all_user_sessions(db, user_id)
        
        db.commit()
        
        logger.info(f"User deactivated by admin: {user.username} by {current_user.username}")
        
        return {"message": "User deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"User deletion failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User deletion failed"
        )


@router.get("/system/stats")
async def get_system_stats(
    current_user: User = Depends(require_admin_access),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get comprehensive system statistics
    """
    try:
        # User statistics
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        users_by_role = {}
        
        for role in UserRole:
            count = db.query(User).filter(User.role == role, User.is_active == True).count()
            users_by_role[role.value] = count
        
        # Chat statistics
        total_messages = db.query(ChatHistory).count()
        messages_last_24h = db.query(ChatHistory).filter(
            ChatHistory.timestamp >= datetime.now() - timedelta(days=1)
        ).count()
        
        unique_sessions = db.query(ChatHistory.session_id).distinct().count()
        
        # Database statistics
        db_stats = db_manager.get_connection_info()
        
        # Vector store statistics
        vector_stats = vector_store.get_collection_stats()
        
        # Data processor statistics
        data_summary = data_processor.get_data_summary(UserRole.C_LEVEL)
        
        # Application metrics
        app_metrics = metrics_middleware.get_metrics()
        
        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "by_role": users_by_role
            },
            "chat": {
                "total_messages": total_messages,
                "messages_last_24h": messages_last_24h,
                "unique_sessions": unique_sessions
            },
            "database": db_stats,
            "vector_store": vector_stats,
            "data_sources": data_summary,
            "application": app_metrics,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system statistics"
        )


@router.post("/system/reindex-data")
async def reindex_data(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin_access)
) -> Dict[str, str]:
    """
    Reindex all data sources in the vector store
    """
    try:
        # Add reindexing task to background
        background_tasks.add_task(perform_reindexing, current_user.username)
        
        logger.info(f"Data reindexing initiated by admin: {current_user.username}")
        
        return {
            "message": "Data reindexing started in background",
            "initiated_by": current_user.username,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to initiate reindexing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate reindexing"
        )


@router.delete("/system/vector-store")
async def reset_vector_store(
    current_user: User = Depends(require_admin_access)
) -> Dict[str, str]:
    """
    Reset vector store (use with caution!)
    """
    try:
        success = vector_store.reset_collection()
        
        if success:
            logger.warning(f"Vector store reset by admin: {current_user.username}")
            return {"message": "Vector store reset successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset vector store"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vector store reset failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Vector store reset failed"
        )


@router.get("/chat/analytics")
async def get_chat_analytics(
    days: int = 7,
    current_user: User = Depends(require_admin_access),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get chat analytics for the specified period
    """
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        # Messages by day
        messages_by_day = db.query(
            db.func.date(ChatHistory.timestamp).label('date'),
            db.func.count(ChatHistory.id).label('count')
        ).filter(
            ChatHistory.timestamp >= start_date
        ).group_by(
            db.func.date(ChatHistory.timestamp)
        ).all()
        
        # Messages by user role
        messages_by_role = db.query(
            User.role,
            db.func.count(ChatHistory.id).label('count')
        ).join(
            ChatHistory, User.id == ChatHistory.user_id
        ).filter(
            ChatHistory.timestamp >= start_date
        ).group_by(User.role).all()
        
        # Most active users
        active_users = db.query(
            User.username,
            User.role,
            db.func.count(ChatHistory.id).label('message_count')
        ).join(
            ChatHistory, User.id == ChatHistory.user_id
        ).filter(
            ChatHistory.timestamp >= start_date
        ).group_by(User.id).order_by(
            db.func.count(ChatHistory.id).desc()
        ).limit(10).all()
        
        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "messages_by_day": [
                {"date": str(item.date), "count": item.count}
                for item in messages_by_day
            ],
            "messages_by_role": [
                {"role": item.role.value, "count": item.count}
                for item in messages_by_role
            ],
            "most_active_users": [
                {
                    "username": item.username,
                    "role": item.role.value,
                    "message_count": item.message_count
                }
                for item in active_users
            ],
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get chat analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat analytics"
        )


@router.post("/system/cleanup")
async def cleanup_system(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin_access),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Cleanup expired sessions and old data
    """
    try:
        # Cleanup expired sessions
        cleaned_sessions = auth_service.cleanup_expired_sessions(db)
        
        # Add background task for additional cleanup
        background_tasks.add_task(perform_system_cleanup, current_user.username)
        
        logger.info(f"System cleanup initiated by admin: {current_user.username}")
        
        return {
            "message": f"System cleanup completed. {cleaned_sessions} expired sessions removed.",
            "initiated_by": current_user.username,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"System cleanup failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="System cleanup failed"
        )


def perform_reindexing(admin_username: str):
    """
    Background task to perform data reindexing
    """
    try:
        logger.info(f"Starting data reindexing initiated by {admin_username}")
        
        # Reset vector store
        vector_store.reset_collection()
        
        # Reindex all data sources
        success = vector_store.index_data_sources()
        
        if success:
            logger.info(f"Data reindexing completed successfully by {admin_username}")
        else:
            logger.error(f"Data reindexing failed for {admin_username}")
            
    except Exception as e:
        logger.error(f"Data reindexing error: {str(e)}")


def perform_system_cleanup(admin_username: str):
    """
    Background task to perform system cleanup
    """
    try:
        logger.info(f"Starting system cleanup initiated by {admin_username}")
        
        # Additional cleanup tasks can be added here
        # For example: cleaning old logs, temporary files, etc.
        
        logger.info(f"System cleanup completed by {admin_username}")
        
    except Exception as e:
        logger.error(f"System cleanup error: {str(e)}")


@router.get("/config")
async def get_system_config(
    current_user: User = Depends(require_admin_access)
) -> Dict[str, Any]:
    """
    Get system configuration
    """
    return {
        "application": {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "debug": settings.debug
        },
        "features": {
            "max_context_length": settings.max_context_length,
            "similarity_threshold": settings.similarity_threshold,
            "max_retrieved_docs": settings.max_retrieved_docs,
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap
        },
        "security": {
            "access_token_expire_minutes": settings.access_token_expire_minutes,
            "bcrypt_rounds": settings.bcrypt_rounds
        },
        "timestamp": time.time()
    }
