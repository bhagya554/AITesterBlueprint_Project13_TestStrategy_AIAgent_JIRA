#!/usr/bin/env python3
"""
Ollama Connectivity Check Tool
Tests connection to local Ollama instance
Usage: python tools/check_ollama.py
"""

import os
import sys
import json
import httpx
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)


def check_ollama_connection():
    """Test Ollama connection and list available models."""
    
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip('/')
    
    print(f"🔍 Testing Ollama connection to: {base_url}")
    
    try:
        # Test /api/tags endpoint
        response = httpx.get(f"{base_url}/api/tags", timeout=5.0)
        
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            
            print(f"\n✅ Ollama connection successful!")
            print(f"   Installed models ({len(models)} total):")
            
            if models:
                for model in models:
                    model_name = model.get("name", "unknown")
                    size_gb = model.get("size", 0) / (1024**3)
                    print(f"     • {model_name} ({size_gb:.1f} GB)")
            else:
                print("     (No models installed)")
                print("\n   To install a model, run:")
                print("     ollama pull llama3.1")
            
            return True, base_url
            
        else:
            print(f"\n❌ Ollama returned HTTP {response.status_code}")
            return False, base_url
            
    except httpx.ConnectError as e:
        print(f"\n❌ Cannot connect to Ollama at {base_url}")
        print(f"   Error: {e}")
        print(f"\n   Is Ollama running? Start it with:")
        print(f"     ollama serve")
        print(f"\n   Or install Ollama from: https://ollama.com/download")
        return False, base_url
        
    except httpx.TimeoutException:
        print(f"\n❌ Connection to Ollama timed out")
        return False, base_url
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {type(e).__name__}: {e}")
        return False, base_url


def test_chat_completion(base_url: str):
    """Test a simple chat completion."""
    
    # Get first available model
    try:
        response = httpx.get(f"{base_url}/api/tags", timeout=5.0)
        models = response.json().get("models", [])
        
        if not models:
            print("\n⚠️  No models installed, skipping chat test")
            return False
        
        model_name = models[0].get("name", "llama3.1")
        
        print(f"\n🧪 Testing chat with model: {model_name}")
        
        # Simple chat test
        chat_response = httpx.post(
            f"{base_url}/api/chat",
            json={
                "model": model_name,
                "messages": [
                    {"role": "user", "content": "Say 'Ollama is working' in 5 words or less."}
                ],
                "stream": False
            },
            timeout=30.0
        )
        
        if chat_response.status_code == 200:
            data = chat_response.json()
            message = data.get("message", {}).get("content", "")
            print(f"   Response: '{message[:50]}...'")
            print("\n✅ Chat test successful!")
            return True
        else:
            print(f"\n❌ Chat test failed: HTTP {chat_response.status_code}")
            print(f"   {chat_response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"\n❌ Chat test error: {e}")
        return False


def test_streaming(base_url: str):
    """Test streaming chat completion."""
    
    try:
        response = httpx.get(f"{base_url}/api/tags", timeout=5.0)
        models = response.json().get("models", [])
        
        if not models:
            return False
        
        model_name = models[0].get("name", "llama3.1")
        
        print(f"\n🌊 Testing streaming with {model_name}...")
        
        with httpx.stream(
            "POST",
            f"{base_url}/api/chat",
            json={
                "model": model_name,
                "messages": [
                    {"role": "user", "content": "Count: 1, 2, 3"}
                ],
                "stream": True
            },
            timeout=30.0
        ) as stream:
            
            chunks = []
            for line in stream.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if data.get("message", {}).get("content"):
                            chunks.append(data["message"]["content"])
                    except json.JSONDecodeError:
                        pass
            
            result = "".join(chunks)
            print(f"   Streamed: '{result[:50]}...'")
            print("\n✅ Streaming test passed!")
            return True
            
    except Exception as e:
        print(f"\n❌ Streaming test failed: {e}")
        return False


def check_ollama_version(base_url: str):
    """Get Ollama version."""
    try:
        response = httpx.get(f"{base_url}/api/version", timeout=5.0)
        if response.status_code == 200:
            version = response.json().get("version", "unknown")
            print(f"\n📦 Ollama version: {version}")
    except:
        pass


if __name__ == "__main__":
    print("=" * 50)
    print("Ollama Connectivity Check Tool")
    print("=" * 50)
    
    success, base_url = check_ollama_connection()
    
    if success:
        check_ollama_version(base_url)
        test_chat_completion(base_url)
        test_streaming(base_url)
        print("\n" + "=" * 50)
        print("✅ All Ollama checks passed!")
        print("=" * 50)
        sys.exit(0)
    else:
        print("\n" + "=" * 50)
        print("❌ Ollama checks failed.")
        print("=" * 50)
        sys.exit(1)
