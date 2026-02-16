"""
LLM Provider Abstraction
Supports Groq and Ollama with unified interface
"""

import os
import json
import asyncio
from typing import AsyncGenerator, List, Optional, Dict, Any
from abc import ABC, abstractmethod
import httpx

from config import get_settings


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> AsyncGenerator[str, None]:
        """Generate text with streaming response."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to the provider."""
        pass
    
    @abstractmethod
    async def list_models(self) -> List[str]:
        """List available models."""
        pass


class GroqProvider(LLMProvider):
    """Groq LLM provider."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_settings().groq_api_key
        self._client = None
    
    def _get_client(self):
        """Lazy load Groq client."""
        if self._client is None:
            from groq import AsyncGroq
            self._client = AsyncGroq(api_key=self.api_key)
        return self._client
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> AsyncGenerator[str, None]:
        """Stream generation from Groq."""
        client = self._get_client()
        
        try:
            stream = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content
                    
        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "429" in error_msg:
                raise RateLimitError(f"Groq rate limit: {e}")
            elif "authentication" in error_msg or "401" in error_msg:
                raise AuthenticationError(f"Groq authentication failed: {e}")
            elif "context" in error_msg and "length" in error_msg:
                raise ContextLengthError(f"Context too long: {e}")
            else:
                raise LLMError(f"Groq error: {e}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Groq connection."""
        try:
            client = self._get_client()
            models = await client.models.list()
            
            return {
                "success": True,
                "models_count": len(models.data),
                "message": "Connected to Groq API"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to connect to Groq API"
            }
    
    async def list_models(self) -> List[str]:
        """List available Groq models."""
        try:
            client = self._get_client()
            models = await client.models.list()
            
            # Return preferred models first, then all others
            preferred = [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "deepseek-r1-distill-llama-70b",
                "qwen-qwq-32b",
                "meta-llama/llama-4-scout-17b-16e-instruct"
            ]
            
            available = [m.id for m in models.data]
            
            # Sort: preferred first (in order), then others alphabetically
            result = []
            for pref in preferred:
                matching = [m for m in available if pref in m]
                result.extend(matching)
            
            # Add any remaining models
            for m in available:
                if m not in result:
                    result.append(m)
            
            return result
        except Exception:
            return preferred  # Return defaults on error


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or get_settings().ollama_base_url).rstrip('/')
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> AsyncGenerator[str, None]:
        """Stream generation from Ollama."""
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_ctx": 32768,  # Important: Ollama defaults to 4K
                "num_predict": max_tokens
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", url, json=payload, timeout=300.0) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        raise LLMError(f"Ollama error: {error_text}")
                    
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                
                                # Check for error in response
                                if data.get("error"):
                                    raise LLMError(f"Ollama: {data['error']}")
                                
                                # Extract content
                                message = data.get("message", {})
                                content = message.get("content", "")
                                
                                if content:
                                    yield content
                                
                                # Check if done
                                if data.get("done", False):
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                                
        except httpx.ConnectError:
            raise ConnectionError(f"Cannot connect to Ollama at {self.base_url}. Is it running?")
        except Exception as e:
            if "not found" in str(e).lower():
                raise LLMError(f"Model not found. Pull it first: ollama pull {model}")
            raise LLMError(f"Ollama error: {e}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Ollama connection."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    return {
                        "success": True,
                        "models_count": len(models),
                        "message": f"Connected to Ollama at {self.base_url}"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "message": "Ollama returned error"
                    }
        except httpx.ConnectError:
            return {
                "success": False,
                "error": "Connection refused",
                "message": f"Cannot connect to Ollama at {self.base_url}. Start with: ollama serve"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to connect to Ollama"
            }
    
    async def list_models(self) -> List[str]:
        """List available Ollama models."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    return [m.get("name", "") for m in models]
                return []
        except Exception:
            return []


# Exception classes
class LLMError(Exception):
    """Base LLM error."""
    pass


class RateLimitError(LLMError):
    """Rate limit exceeded."""
    pass


class AuthenticationError(LLMError):
    """Authentication failed."""
    pass


class ContextLengthError(LLMError):
    """Context length exceeded."""
    pass


class ConnectionError(LLMError):
    """Connection error."""
    pass


def get_provider(provider_name: str) -> LLMProvider:
    """Factory function to get appropriate provider."""
    settings = get_settings()
    
    if provider_name.lower() == "groq":
        return GroqProvider(settings.groq_api_key)
    elif provider_name.lower() == "ollama":
        return OllamaProvider(settings.ollama_base_url)
    else:
        raise ValueError(f"Unknown provider: {provider_name}")


def estimate_tokens(text: str) -> int:
    """
    Rough token estimation.
    Uses ~4 characters per token for English text as a heuristic.
    """
    if not text:
        return 0
    return len(text) // 4


def get_model_limits(provider: str, model: str) -> Dict[str, int]:
    """Get context window and max output for a model."""
    
    # Groq models
    groq_limits = {
        "llama-3.3-70b-versatile": {"context": 131072, "output": 32768},
        "llama-3.1-8b-instant": {"context": 131072, "output": 131072},
        "deepseek-r1-distill-llama-70b": {"context": 131072, "output": 16384},
        "qwen-qwq-32b": {"context": 131072, "output": 16384},
        "meta-llama/llama-4-scout-17b-16e-instruct": {"context": 131072, "output": 8192},
    }
    
    # Ollama models (varies by actual model, these are common)
    ollama_limits = {
        "llama3.1": {"context": 128000, "output": 4096},
        "llama3.1:70b": {"context": 128000, "output": 4096},
        "mistral": {"context": 32000, "output": 4096},
        "qwen2.5": {"context": 128000, "output": 4096},
        "gemma2": {"context": 8000, "output": 4096},
    }
    
    if provider.lower() == "groq":
        for key, limits in groq_limits.items():
            if key in model:
                return limits
        return {"context": 131072, "output": 8192}  # Default
    
    elif provider.lower() == "ollama":
        for key, limits in ollama_limits.items():
            if key in model:
                return limits
        return {"context": 32768, "output": 4096}  # Safe default
    
    return {"context": 8192, "output": 4096}
