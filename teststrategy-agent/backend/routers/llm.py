"""
LLM API Router
Endpoints for testing LLM connections and listing models
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from models import Provider, LLMTestRequest, LLMModelsResponse, LLMProvidersResponse
from services.llm_provider import get_provider
from config import get_settings

router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.get("/providers")
async def list_providers() -> List[Dict[str, Any]]:
    """List available LLM providers and their connection status."""
    settings = get_settings()
    providers = []
    
    # Groq
    try:
        groq = get_provider("groq")
        groq_test = await groq.test_connection()
        providers.append({
            "name": "groq",
            "display_name": "Groq",
            "connected": groq_test.get("success", False),
            "default_model": settings.groq_default_model,
            "message": groq_test.get("message", ""),
            "api_key_set": bool(settings.groq_api_key)
        })
    except Exception as e:
        providers.append({
            "name": "groq",
            "display_name": "Groq",
            "connected": False,
            "default_model": settings.groq_default_model,
            "message": str(e),
            "api_key_set": bool(settings.groq_api_key)
        })
    
    # Ollama
    try:
        ollama = get_provider("ollama")
        ollama_test = await ollama.test_connection()
        providers.append({
            "name": "ollama",
            "display_name": "Ollama (Local)",
            "connected": ollama_test.get("success", False),
            "default_model": settings.ollama_default_model,
            "message": ollama_test.get("message", ""),
            "base_url": settings.ollama_base_url
        })
    except Exception as e:
        providers.append({
            "name": "ollama",
            "display_name": "Ollama (Local)",
            "connected": False,
            "default_model": settings.ollama_default_model,
            "message": str(e),
            "base_url": settings.ollama_base_url
        })
    
    return providers


@router.get("/models/{provider}", response_model=LLMModelsResponse)
async def list_models(provider: Provider) -> LLMModelsResponse:
    """List available models for a provider."""
    settings = get_settings()
    
    try:
        provider_instance = get_provider(provider.value)
        models = await provider_instance.list_models()
        
        default_model = (
            settings.groq_default_model if provider == Provider.GROQ 
            else settings.ollama_default_model
        )
        
        return LLMModelsResponse(
            provider=provider.value,
            models=models,
            default_model=default_model
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_llm_connection(request: LLMTestRequest):
    """Test connection to an LLM provider with a simple prompt."""
    try:
        provider = get_provider(request.provider.value)
        
        # Test basic connection
        test_result = await provider.test_connection()
        
        if not test_result.get("success"):
            raise HTTPException(status_code=400, detail=test_result.get("message", "Connection failed"))
        
        # If model specified, test actual generation
        if request.model:
            chunks = []
            async for chunk in provider.generate_stream(
                prompt="Say 'Test passed' in exactly 2 words.",
                system_prompt="You are a test assistant. Be brief.",
                model=request.model,
                temperature=0.0,
                max_tokens=10
            ):
                chunks.append(chunk)
            
            response = "".join(chunks)
            
            return {
                "success": True,
                "connection_test": test_result,
                "generation_test": {
                    "success": True,
                    "response": response[:100]
                }
            }
        
        return {
            "success": True,
            "connection_test": test_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
