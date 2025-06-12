"""
Chat Routes for FinSolve RBAC Chatbot API
Main chat endpoints for processing user queries with role-based access control,
hybrid MCP + RAG approach, and comprehensive response generation.

Author: Peter Pandey
Version: 1.0.0
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List, Optional
import uuid
import time
import json
from datetime import datetime
from loguru import logger

from ...database.connection import get_db
from ...auth.models import User, ChatMessage, ChatResponse, ChatHistory
from ...agents.graph import finsolve_agent
from ...data.processors import data_processor
from ...rag.vector_store import vector_store
from ...core.config import UserRole
from ..dependencies import get_current_active_user, get_request_context

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    request_context: Dict = Depends(get_request_context)
) -> ChatResponse:
    """
    Process a chat message and return AI-generated response
    """
    start_time = datetime.now()
    session_id = message.session_id or str(uuid.uuid4())
    
    try:
        # Validate message content
        if not message.content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message content cannot be empty"
            )
        
        # Log user message
        background_tasks.add_task(
            save_chat_history,
            db,
            current_user.id,
            session_id,
            "user",
            message.content,
            request_context
        )
        
        # Process query through LangGraph agent
        response = await finsolve_agent.process_query(
            query=message.content,
            user=current_user,
            session_id=session_id
        )
        
        # Create enhanced response object
        chat_response = ChatResponse(
            content=response.content,
            short_answer=response.short_answer,
            detailed_response=response.detailed_response,
            summary=response.summary,
            message_type="assistant",
            session_id=session_id,
            retrieved_documents=response.sources,
            confidence_score=response.confidence_score,
            processing_time=response.processing_time,
            timestamp=datetime.now(),
            visualization=response.visualization,
            conversation_context=response.conversation_context
        )
        
        # Log assistant response
        background_tasks.add_task(
            save_chat_history,
            db,
            current_user.id,
            session_id,
            "assistant",
            response.content,
            {
                **request_context,
                "sources": response.sources,
                "confidence_score": response.confidence_score,
                "query_type": response.query_type.value,
                "metadata": response.metadata
            }
        )
        
        logger.info(
            f"Chat message processed - User: {current_user.username} | "
            f"Session: {session_id} | "
            f"Processing time: {response.processing_time:.3f}s | "
            f"Confidence: {response.confidence_score:.3f}"
        )
        
        return chat_response
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.error(
            f"Chat message processing failed - User: {current_user.username} | "
            f"Session: {session_id} | "
            f"Error: {str(e)}"
        )
        
        # Log error message
        background_tasks.add_task(
            save_chat_history,
            db,
            current_user.id,
            session_id,
            "assistant",
            f"I apologize, but I encountered an error while processing your request: {str(e)}",
            {**request_context, "error": str(e)}
        )
        
        return ChatResponse(
            content="I apologize, but I encountered an error while processing your request. Please try again or contact support if the issue persists.",
            message_type="assistant",
            session_id=session_id,
            retrieved_documents=[],
            confidence_score=0.0,
            processing_time=processing_time,
            timestamp=datetime.now()
        )


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get chat history for a specific session
    """
    try:
        # Query chat history
        history_query = db.query(ChatHistory).filter(
            ChatHistory.session_id == session_id,
            ChatHistory.user_id == current_user.id
        ).order_by(ChatHistory.timestamp.desc())
        
        # Apply pagination
        total_count = history_query.count()
        history_items = history_query.offset(offset).limit(limit).all()
        
        # Format response
        messages = []
        for item in reversed(history_items):  # Reverse to get chronological order
            message_data = {
                "id": item.id,
                "content": item.content,
                "message_type": item.message_type,
                "timestamp": item.timestamp.isoformat(),
                "metadata": json.loads(item.message_metadata) if item.message_metadata else {}
            }
            
            # Add RAG-specific fields for assistant messages
            if item.message_type == "assistant":
                message_data.update({
                    "retrieved_documents": json.loads(item.retrieved_documents) if item.retrieved_documents else [],
                    "confidence_score": float(item.confidence_score) if item.confidence_score else None,
                    "processing_time": float(item.processing_time) if item.processing_time else None
                })
            
            messages.append(message_data)
        
        return {
            "session_id": session_id,
            "messages": messages,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get chat history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat history"
        )


@router.get("/sessions")
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get all chat sessions for the current user
    """
    try:
        # Query distinct sessions
        sessions_query = db.query(
            ChatHistory.session_id,
            func.min(ChatHistory.timestamp).label('first_message'),
            func.max(ChatHistory.timestamp).label('last_message'),
            func.count(ChatHistory.id).label('message_count')
        ).filter(
            ChatHistory.user_id == current_user.id
        ).group_by(ChatHistory.session_id).order_by(
            func.max(ChatHistory.timestamp).desc()
        )
        
        sessions = sessions_query.all()
        
        # Format response
        session_list = []
        for session in sessions:
            # Get the first user message as session title
            first_user_message = db.query(ChatHistory).filter(
                ChatHistory.session_id == session.session_id,
                ChatHistory.user_id == current_user.id,
                ChatHistory.message_type == "user"
            ).order_by(ChatHistory.timestamp.asc()).first()
            
            title = "New Chat"
            if first_user_message:
                title = first_user_message.content[:50] + "..." if len(first_user_message.content) > 50 else first_user_message.content
            
            session_list.append({
                "session_id": session.session_id,
                "title": title,
                "first_message": session.first_message.isoformat(),
                "last_message": session.last_message.isoformat(),
                "message_count": session.message_count
            })
        
        return {
            "sessions": session_list,
            "total_sessions": len(session_list),
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get user sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Delete a chat session and all its messages
    """
    try:
        # Delete all messages in the session
        deleted_count = db.query(ChatHistory).filter(
            ChatHistory.session_id == session_id,
            ChatHistory.user_id == current_user.id
        ).delete()
        
        db.commit()
        
        logger.info(f"Session deleted: {session_id} by {current_user.username} ({deleted_count} messages)")
        
        return {
            "message": f"Session deleted successfully ({deleted_count} messages removed)",
            "session_id": session_id
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )


@router.get("/data-summary")
async def get_data_summary(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get summary of available data sources for the current user
    """
    try:
        # Get data summary from processor
        summary = data_processor.get_data_summary(current_user.role)
        
        # Get vector store stats
        vector_stats = vector_store.get_collection_stats()
        
        return {
            "user_role": current_user.role.value,
            "data_sources": summary,
            "vector_store": vector_stats,
            "capabilities": {
                "structured_data_query": True,
                "document_search": True,
                "hybrid_queries": True,
                "role_based_filtering": True
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get data summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve data summary"
        )


@router.post("/search")
async def search_documents(
    search_request: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Search documents directly without chat interface
    """
    try:
        query = search_request.get("query", "")
        department_filter = search_request.get("department")
        limit = min(search_request.get("limit", 5), 20)  # Max 20 results
        
        if not query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query cannot be empty"
            )
        
        # Search vector store
        search_results = vector_store.search(
            query=query,
            user_role=current_user.role,
            n_results=limit,
            department_filter=department_filter
        )
        
        # Format results
        results = []
        for result in search_results:
            results.append({
                "content": result.document.content,
                "metadata": result.document.metadata,
                "similarity_score": result.similarity_score,
                "rank": result.rank
            })
        
        return {
            "query": query,
            "results": results,
            "total_results": len(results),
            "department_filter": department_filter,
            "user_role": current_user.role.value,
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


def save_chat_history(
    db: Session,
    user_id: int,
    session_id: str,
    message_type: str,
    content: str,
    metadata: Dict[str, Any]
):
    """
    Background task to save chat history
    """
    try:
        chat_entry = ChatHistory(
            session_id=session_id,
            user_id=user_id,
            message_type=message_type,
            content=content,
            message_metadata=json.dumps(metadata) if metadata else None,
            retrieved_documents=json.dumps(metadata.get("sources", [])) if metadata.get("sources") else None,
            confidence_score=str(metadata.get("confidence_score")) if metadata.get("confidence_score") is not None else None,
            processing_time=str(metadata.get("processing_time")) if metadata.get("processing_time") is not None else None
        )
        
        db.add(chat_entry)
        db.commit()
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save chat history: {str(e)}")


@router.get("/suggestions")
async def get_query_suggestions(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get query suggestions based on user role
    """
    suggestions = {
        UserRole.EMPLOYEE: [
            "What is our leave policy?",
            "How do I submit a reimbursement?",
            "What are the company holidays?",
            "Where can I find the employee handbook?",
            "What are our core values?"
        ],
        UserRole.HR: [
            "Show me employee performance ratings",
            "What is the average salary in the Technology department?",
            "How many employees joined this quarter?",
            "What is our current headcount by department?",
            "Show me attendance records for this month"
        ],
        UserRole.FINANCE: [
            "What was our Q4 revenue?",
            "Show me the latest financial report",
            "What are our major expenses this year?",
            "How much did we spend on marketing?",
            "What is our profit margin trend?"
        ],
        UserRole.MARKETING: [
            "What was our customer acquisition cost?",
            "Show me the latest marketing campaign results",
            "What is our brand awareness growth?",
            "How effective were our digital campaigns?",
            "What is our return on ad spend?"
        ],
        UserRole.ENGINEERING: [
            "What is our system architecture?",
            "Show me the development processes",
            "What technologies do we use?",
            "How do we handle security?",
            "What is our deployment pipeline?"
        ],
        UserRole.C_LEVEL: [
            "Give me a company overview",
            "What are our key performance metrics?",
            "Show me financial and operational highlights",
            "What are our strategic initiatives?",
            "How are we performing against our goals?"
        ]
    }
    
    user_suggestions = suggestions.get(current_user.role, suggestions[UserRole.EMPLOYEE])
    
    return {
        "suggestions": user_suggestions,
        "user_role": current_user.role.value,
        "timestamp": time.time()
    }
