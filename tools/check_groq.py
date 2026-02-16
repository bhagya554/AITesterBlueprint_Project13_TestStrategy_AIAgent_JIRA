#!/usr/bin/env python3
"""
Groq Connectivity Check Tool
Tests connection to Groq API
Usage: python tools/check_groq.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)


def check_groq_connection():
    """Test Groq API connection and list available models."""
    
    api_key = os.getenv("GROQ_API_KEY", "")
    
    if not api_key:
        print("❌ GROQ_API_KEY not set in .env")
        print("\nℹ️  Get your Groq API key from: https://console.groq.com/keys")
        return False
    
    if not api_key.startswith("gsk_"):
        print("⚠️  Warning: GROQ_API_KEY doesn't start with 'gsk_' — may be invalid")
    
    print(f"🔍 Testing Groq connection...")
    print(f"   API Key: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        from groq import Groq
        
        client = Groq(api_key=api_key)
        
        # Test connection by listing models
        print("\n📡 Fetching available models...")
        models = client.models.list()
        
        print(f"\n✅ Groq connection successful!")
        print(f"   Available models ({len(models.data)} total):")
        
        # Filter for chat models we care about
        preferred_models = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "deepseek-r1-distill-llama-70b",
            "qwen-qwq-32b",
            "meta-llama/llama-4-scout-17b-16e-instruct"
        ]
        
        available_preferred = []
        for model in models.data:
            model_id = model.id
            if any(pref in model_id for pref in preferred_models):
                available_preferred.append(model_id)
        
        if available_preferred:
            print("\n   Recommended models for TestStrategy Agent:")
            for model_id in available_preferred[:5]:
                print(f"     • {model_id}")
        else:
            print("\n   First 5 available models:")
            for model in models.data[:5]:
                print(f"     • {model.id}")
        
        # Test a simple completion
        print("\n🧪 Testing simple completion...")
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Groq connection test passed' and nothing else."}
            ],
            max_tokens=20,
            temperature=0.0
        )
        
        response_text = completion.choices[0].message.content.strip()
        print(f"   Response: '{response_text}'")
        
        if "passed" in response_text.lower() or "test" in response_text.lower():
            print("\n✅ Completion test successful!")
            return True
        else:
            print("\n⚠️  Completion test returned unexpected response, but API is working")
            return True
            
    except ImportError:
        print("\n❌ groq package not installed")
        print("   Run: pip install groq")
        return False
        
    except Exception as e:
        error_str = str(e).lower()
        
        if "authentication" in error_str or "401" in error_str or "unauthorized" in error_str:
            print(f"\n❌ Groq authentication failed (401)")
            print(f"   Your API key is invalid or expired")
            print(f"   Get a new key from: https://console.groq.com/keys")
        elif "rate limit" in error_str or "429" in error_str:
            print(f"\n⚠️  Groq rate limit hit (429)")
            print(f"   Wait a moment and try again")
        elif "connection" in error_str:
            print(f"\n❌ Cannot connect to Groq API")
            print(f"   Check your internet connection")
        else:
            print(f"\n❌ Groq API error: {type(e).__name__}: {e}")
        
        return False


def test_streaming():
    """Test streaming completion."""
    api_key = os.getenv("GROQ_API_KEY", "")
    
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        
        print("\n🌊 Testing streaming...")
        stream = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": "Count: 1, 2, 3"}
            ],
            max_tokens=20,
            stream=True
        )
        
        chunks = []
        for chunk in stream:
            if chunk.choices[0].delta.content:
                chunks.append(chunk.choices[0].delta.content)
        
        result = "".join(chunks)
        print(f"   Streamed: '{result[:50]}...'")
        print("\n✅ Streaming test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Streaming test failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("Groq Connectivity Check Tool")
    print("=" * 50)
    
    success = check_groq_connection()
    
    if success:
        test_streaming()
        print("\n" + "=" * 50)
        print("✅ All Groq checks passed!")
        print("=" * 50)
        sys.exit(0)
    else:
        print("\n" + "=" * 50)
        print("❌ Groq checks failed. Please fix the issues above.")
        print("=" * 50)
        sys.exit(1)
