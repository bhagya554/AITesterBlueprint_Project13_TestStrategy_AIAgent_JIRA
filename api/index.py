"""
Vercel Serverless Adapter for TestStrategy Agent
"""
import os
import sys

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'teststrategy-agent', 'backend')
sys.path.insert(0, backend_path)

# Change to backend directory for relative paths
os.chdir(backend_path)

from main import app

# Vercel handler
from fastapi import Request
from fastapi.responses import JSONResponse

@app.get("/api/health")
async def vercel_health():
    return {"status": "healthy", "service": "TestStrategy Agent on Vercel"}

# Export for Vercel
handler = app
