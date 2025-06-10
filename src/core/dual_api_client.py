#!/usr/bin/env python3
"""
Dual API Client - Euri Primary, OpenAI Fallback
Provides reliable LLM responses with automatic fallback from Euri to OpenAI.

Author: Peter Pandey
Version: 1.0.0
"""

import os
import time
import threading
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from .config import settings

# Try to import OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

# Try to import Euriai LangChain
try:
    from euriai import EuriaiLangChainLLM
    EURIAI_LANGCHAIN_AVAILABLE = True
except ImportError:
    EURIAI_LANGCHAIN_AVAILABLE = False
    EuriaiLangChainLLM = None

from .euri_client import euri_client


@dataclass
class APIResponse:
    """Standardized API response"""
    success: bool
    content: str
    api_used: str
    response_time: float
    model: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class DualAPIClient:
    """
    Dual API client with Euri as primary and OpenAI as fallback
    Provides reliable LLM responses with automatic failover
    """
    
    def __init__(self):
        self.euri_api_key = settings.euri_api_key
        self.openai_api_key = settings.openai_api_key
        
        # Initialize Euriai LangChain if available
        self.euriai_llm = None
        if EURIAI_LANGCHAIN_AVAILABLE and self.euri_api_key:
            try:
                self.euriai_llm = EuriaiLangChainLLM(
                    api_key=self.euri_api_key,
                    model="gpt-4.1-nano",
                    temperature=0.7,
                    max_tokens=settings.openai_max_tokens
                )
                logger.info("Euriai LangChain LLM initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Euriai LangChain: {str(e)}")
        
        # Initialize OpenAI if available
        self.openai_client = None
        if OPENAI_AVAILABLE and self.openai_api_key:
            try:
                self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {str(e)}")
        
        logger.info(f"Dual API client initialized - Euri: {bool(self.euriai_llm)}, OpenAI: {bool(self.openai_client)}")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout: int = 30
    ) -> APIResponse:
        """
        Get chat completion with automatic fallback
        Tries Euri first, then OpenAI if Euri fails
        """
        
        # Convert messages to prompt for single-prompt APIs
        prompt = self._messages_to_prompt(messages)
        
        # Try Euriai first
        euri_response = self._try_euriai(prompt, temperature, max_tokens, timeout)
        if euri_response.success:
            return euri_response
        
        # Try regular Euri client
        euri_client_response = self._try_euri_client(messages, temperature, max_tokens)
        if euri_client_response.success:
            return euri_client_response
        
        # Fallback to OpenAI
        openai_response = self._try_openai(messages, temperature, max_tokens, timeout)
        if openai_response.success:
            return openai_response
        
        # All APIs failed
        return APIResponse(
            success=False,
            content="",
            api_used="none",
            response_time=0.0,
            model="none",
            error=f"All APIs failed - Euri: {euri_response.error}, OpenAI: {openai_response.error}"
        )
    
    def _try_euriai(self, prompt: str, temperature: float, max_tokens: int, timeout: int) -> APIResponse:
        """Try Euriai LangChain with timeout"""
        if not self.euriai_llm:
            return APIResponse(
                success=False,
                content="",
                api_used="euriai",
                response_time=0.0,
                model="gpt-4.1-nano",
                error="Euriai LangChain not available"
            )
        
        start_time = time.time()
        
        try:
            # Use threading for timeout on Windows
            result = None
            exception_occurred = None
            
            def euriai_call():
                nonlocal result, exception_occurred
                try:
                    result = self.euriai_llm.invoke(prompt)
                except Exception as e:
                    exception_occurred = e
            
            thread = threading.Thread(target=euriai_call)
            thread.daemon = True
            thread.start()
            thread.join(timeout=timeout)
            
            response_time = time.time() - start_time
            
            if thread.is_alive():
                return APIResponse(
                    success=False,
                    content="",
                    api_used="euriai",
                    response_time=response_time,
                    model="gpt-4.1-nano",
                    error=f"Timeout after {timeout}s"
                )
            
            if exception_occurred:
                return APIResponse(
                    success=False,
                    content="",
                    api_used="euriai",
                    response_time=response_time,
                    model="gpt-4.1-nano",
                    error=str(exception_occurred)
                )
            
            if result and not result.startswith("Error:"):
                return APIResponse(
                    success=True,
                    content=result,
                    api_used="euriai",
                    response_time=response_time,
                    model="gpt-4.1-nano"
                )
            else:
                return APIResponse(
                    success=False,
                    content="",
                    api_used="euriai",
                    response_time=response_time,
                    model="gpt-4.1-nano",
                    error="Invalid response from Euriai"
                )
                
        except Exception as e:
            return APIResponse(
                success=False,
                content="",
                api_used="euriai",
                response_time=time.time() - start_time,
                model="gpt-4.1-nano",
                error=str(e)
            )
    
    def _try_euri_client(self, messages: List[Dict[str, str]], temperature: float, max_tokens: int) -> APIResponse:
        """Try regular Euri client"""
        start_time = time.time()
        
        try:
            response = euri_client.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            response_time = time.time() - start_time
            
            if response.success:
                return APIResponse(
                    success=True,
                    content=response.content,
                    api_used="euri_client",
                    response_time=response_time,
                    model=response.model
                )
            else:
                return APIResponse(
                    success=False,
                    content="",
                    api_used="euri_client",
                    response_time=response_time,
                    model="unknown",
                    error=response.error
                )
                
        except Exception as e:
            return APIResponse(
                success=False,
                content="",
                api_used="euri_client",
                response_time=time.time() - start_time,
                model="unknown",
                error=str(e)
            )
    
    def _try_openai(self, messages: List[Dict[str, str]], temperature: float, max_tokens: int, timeout: int) -> APIResponse:
        """Try OpenAI API"""
        if not self.openai_client:
            return APIResponse(
                success=False,
                content="",
                api_used="openai",
                response_time=0.0,
                model=settings.openai_model,
                error="OpenAI client not available"
            )
        
        start_time = time.time()
        
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout
            )
            
            response_time = time.time() - start_time
            
            if response.choices and response.choices[0].message:
                return APIResponse(
                    success=True,
                    content=response.choices[0].message.content,
                    api_used="openai",
                    response_time=response_time,
                    model=settings.openai_model,
                    metadata={
                        "usage": response.usage.dict() if response.usage else None,
                        "finish_reason": response.choices[0].finish_reason
                    }
                )
            else:
                return APIResponse(
                    success=False,
                    content="",
                    api_used="openai",
                    response_time=response_time,
                    model=settings.openai_model,
                    error="No valid response from OpenAI"
                )
                
        except Exception as e:
            return APIResponse(
                success=False,
                content="",
                api_used="openai",
                response_time=time.time() - start_time,
                model=settings.openai_model,
                error=str(e)
            )
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages format to single prompt"""
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of both APIs"""
        return {
            "euriai_available": bool(self.euriai_llm),
            "openai_available": bool(self.openai_client),
            "euri_client_available": bool(euri_client),
            "primary_api": "euriai",
            "fallback_api": "openai"
        }


# Global dual API client instance
dual_api_client = DualAPIClient()
