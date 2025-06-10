"""
Euri API Client for FinSolve RBAC Chatbot
Production-grade implementation with comprehensive error handling,
logging, retry logic, and async support.

Author: Peter Pandey
Version: 1.0.0
"""

import asyncio
import time
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
import requests
import httpx
import os
from dotenv import load_dotenv
from loguru import logger
import json

# Load environment variables
load_dotenv()

# Try to import Euriai LangChain components
try:
    from euriai import EuriaiLangChainLLM
    EURIAI_LANGCHAIN_AVAILABLE = True
except ImportError:
    EURIAI_LANGCHAIN_AVAILABLE = False
    EuriaiLangChainLLM = None


class EuriModel(Enum):
    """Available Euri models with their specifications"""
    GPT_4_1_NANO = "gpt-4.1-nano"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5_TURBO = "gpt-3.5-turbo"


@dataclass
class EuriResponse:
    """Structured response from Euri API"""
    content: str
    model: str
    usage: Dict[str, int]
    response_time: float
    success: bool
    error: Optional[str] = None


@dataclass
class EuriMessage:
    """Message structure for Euri API"""
    role: str  # "system", "user", "assistant"
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


class EuriClientError(Exception):
    """Custom exception for Euri client errors"""
    pass


class EuriLangChainWrapper:
    """
    LangChain-compatible wrapper for Euriai LLM
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("EURI_API_KEY")
        self.langchain_llm = None

        if EURIAI_LANGCHAIN_AVAILABLE and self.api_key:
            try:
                self.langchain_llm = EuriaiLangChainLLM(
                    api_key=self.api_key,
                    model="gpt-4.1-nano",
                    temperature=0.7,
                    max_tokens=2000,  # Increased for more detailed responses
                    timeout=60  # Explicit timeout setting
                )
                logger.info("Euriai LangChain LLM initialized successfully with extended timeout")
            except Exception as e:
                logger.warning(f"Failed to initialize Euriai LangChain LLM: {str(e)}")
                self.langchain_llm = None
        else:
            logger.info("Euriai LangChain LLM not available, using fallback")

    def invoke(self, prompt: str) -> str:
        """Invoke the LLM with a prompt"""
        if self.langchain_llm:
            try:
                return self.langchain_llm.invoke(prompt)
            except Exception as e:
                logger.error(f"Euriai LangChain LLM invocation failed: {str(e)}")
                return f"Error: {str(e)}"
        else:
            return "Euriai LangChain LLM not available"

    def is_available(self) -> bool:
        """Check if Euriai LangChain LLM is available"""
        return self.langchain_llm is not None


class EuriClient:
    """
    Production-grade Euri API client with comprehensive features:
    - Async and sync support
    - Retry logic with exponential backoff
    - Rate limiting
    - Comprehensive logging
    - Error handling and recovery
    - Token usage tracking
    - LangChain integration support
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.euron.one/api/v1/euri/alpha/chat/completions",
        timeout: int = 60,  # Increased from 30 to 60 seconds
        max_retries: int = 2,  # Reduced retries to avoid long waits
        retry_delay: float = 2.0,  # Increased delay between retries
        rate_limit_per_minute: int = 30  # Reduced rate limit to be more conservative
    ):
        self.api_key = api_key or os.getenv("EURI_API_KEY")
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit_per_minute = rate_limit_per_minute
        
        # Rate limiting
        self._request_times: List[float] = []
        
        # Validate API key
        if not self.api_key:
            raise EuriClientError("EURI_API_KEY not found in environment variables")
        
        # Setup headers
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "FinSolve-RBAC-Chatbot/1.0.0"
        }
        
        logger.info("Euri client initialized successfully")
    
    def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting"""
        current_time = time.time()
        
        # Remove requests older than 1 minute
        self._request_times = [
            req_time for req_time in self._request_times 
            if current_time - req_time < 60
        ]
        
        # Check if we're hitting rate limit
        if len(self._request_times) >= self.rate_limit_per_minute:
            sleep_time = 60 - (current_time - self._request_times[0])
            if sleep_time > 0:
                logger.warning(f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        self._request_times.append(current_time)
    
    def _prepare_payload(
        self,
        messages: List[Union[EuriMessage, Dict[str, str]]],
        model: Union[EuriModel, str] = EuriModel.GPT_4_1_NANO,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare API request payload"""
        
        # Convert messages to proper format
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, EuriMessage):
                formatted_messages.append(msg.to_dict())
            elif isinstance(msg, dict):
                formatted_messages.append(msg)
            else:
                raise EuriClientError(f"Invalid message type: {type(msg)}")
        
        # Handle model enum
        model_str = model.value if isinstance(model, EuriModel) else model
        
        payload = {
            "model": model_str,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        return payload
    
    def chat_completion(
        self,
        messages: List[Union[EuriMessage, Dict[str, str]]],
        model: Union[EuriModel, str] = EuriModel.GPT_4_1_NANO,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> EuriResponse:
        """
        Synchronous chat completion with retry logic
        
        Args:
            messages: List of messages for the conversation
            model: Model to use for completion
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters
            
        Returns:
            EuriResponse object with completion data
        """
        start_time = time.time()
        
        try:
            self._check_rate_limit()
            payload = self._prepare_payload(messages, model, temperature, max_tokens, **kwargs)
            
            for attempt in range(self.max_retries + 1):
                try:
                    logger.debug(f"Making API request (attempt {attempt + 1})")
                    
                    response = requests.post(
                        self.base_url,
                        headers=self.headers,
                        json=payload,
                        timeout=self.timeout
                    )
                    response.raise_for_status()
                    
                    response_data = response.json()
                    response_time = time.time() - start_time
                    
                    # Validate response structure
                    if "choices" not in response_data or not response_data["choices"]:
                        raise EuriClientError("Invalid response format: missing choices")
                    
                    content = response_data["choices"][0]["message"]["content"]
                    usage = response_data.get("usage", {})
                    
                    logger.info(f"API request successful in {response_time:.2f}s")
                    
                    return EuriResponse(
                        content=content,
                        model=payload["model"],
                        usage=usage,
                        response_time=response_time,
                        success=True
                    )
                    
                except requests.exceptions.RequestException as e:
                    if attempt == self.max_retries:
                        raise EuriClientError(f"API request failed after {self.max_retries + 1} attempts: {str(e)}")
                    
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {str(e)}")
                    time.sleep(wait_time)
                    
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Chat completion failed: {str(e)}")
            
            return EuriResponse(
                content="",
                model=payload.get("model", "unknown"),
                usage={},
                response_time=response_time,
                success=False,
                error=str(e)
            )
    
    async def achat_completion(
        self,
        messages: List[Union[EuriMessage, Dict[str, str]]],
        model: Union[EuriModel, str] = EuriModel.GPT_4_1_NANO,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> EuriResponse:
        """
        Asynchronous chat completion with retry logic
        """
        start_time = time.time()
        
        try:
            self._check_rate_limit()
            payload = self._prepare_payload(messages, model, temperature, max_tokens, **kwargs)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for attempt in range(self.max_retries + 1):
                    try:
                        logger.debug(f"Making async API request (attempt {attempt + 1})")
                        
                        response = await client.post(
                            self.base_url,
                            headers=self.headers,
                            json=payload
                        )
                        response.raise_for_status()
                        
                        response_data = response.json()
                        response_time = time.time() - start_time
                        
                        if "choices" not in response_data or not response_data["choices"]:
                            raise EuriClientError("Invalid response format: missing choices")
                        
                        content = response_data["choices"][0]["message"]["content"]
                        usage = response_data.get("usage", {})
                        
                        logger.info(f"Async API request successful in {response_time:.2f}s")
                        
                        return EuriResponse(
                            content=content,
                            model=payload["model"],
                            usage=usage,
                            response_time=response_time,
                            success=True
                        )
                        
                    except httpx.RequestError as e:
                        if attempt == self.max_retries:
                            raise EuriClientError(f"Async API request failed after {self.max_retries + 1} attempts: {str(e)}")
                        
                        wait_time = self.retry_delay * (2 ** attempt)
                        logger.warning(f"Async request failed (attempt {attempt + 1}), retrying in {wait_time}s: {str(e)}")
                        await asyncio.sleep(wait_time)
                        
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Async chat completion failed: {str(e)}")
            
            return EuriResponse(
                content="",
                model=payload.get("model", "unknown"),
                usage={},
                response_time=response_time,
                success=False,
                error=str(e)
            )
    
    def create_message(self, role: str, content: str) -> EuriMessage:
        """Helper method to create properly formatted messages"""
        return EuriMessage(role=role, content=content)
    
    def create_system_message(self, content: str) -> EuriMessage:
        """Helper method to create system messages"""
        return EuriMessage(role="system", content=content)
    
    def create_user_message(self, content: str) -> EuriMessage:
        """Helper method to create user messages"""
        return EuriMessage(role="user", content=content)
    
    def create_assistant_message(self, content: str) -> EuriMessage:
        """Helper method to create assistant messages"""
        return EuriMessage(role="assistant", content=content)


# Global client instances
euri_client = EuriClient()
euri_langchain = EuriLangChainWrapper()


# Convenience functions for backward compatibility
def euri_chat_completion(
    messages: List[Union[EuriMessage, Dict[str, str]]],
    model: str = "gpt-4.1-nano",
    temperature: float = 0.7,
    max_tokens: int = 1000
) -> str:
    """
    Legacy function for backward compatibility
    Returns only the content string
    """
    response = euri_client.chat_completion(messages, model, temperature, max_tokens)
    if not response.success:
        raise EuriClientError(response.error or "Unknown error occurred")
    return response.content
