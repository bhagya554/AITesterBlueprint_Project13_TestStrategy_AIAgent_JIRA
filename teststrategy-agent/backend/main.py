"""
TestStrategy Agent - Main FastAPI Application
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import init_db
from routers import jira, llm, template, settings, history, generator


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("Starting TestStrategy Agent...")
    
    # Initialize database
    init_db()
    print("Database initialized")
    
    # Check for template
    template_path = Path("teststrategy.pdf")
    if template_path.exists():
        print(f"Template found: {template_path.absolute()}")
    else:
        print(f"Template not found. Please place teststrategy.pdf in the project root.")
    
    yield
    
    # Shutdown
    print("Shutting down TestStrategy Agent...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="TestStrategy Agent",
        description="AI-powered Test Strategy Document Generator",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # CORS middleware - allow all origins for deployed environment
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(jira.router)
    app.include_router(llm.router)
    app.include_router(template.router)
    app.include_router(settings.router)
    app.include_router(history.router)
    app.include_router(generator.router)
    
    # Static files for production build
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # API health check
    @app.get("/api/health")
    async def health_check():
        return {"status": "healthy", "service": "TestStrategy Agent"}
    
    # Serve frontend index.html at root
    @app.get("/")
    async def root():
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {
            "service": "TestStrategy Agent API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/api/health"
        }
    
    # Serve frontend for all non-API routes (SPA mode)
    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        # Skip API and static routes
        if path.startswith("api/") or path.startswith("static/"):
            return {"detail": "Not found"}
        
        # Try to serve index.html for SPA routing
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        
        return {"service": "TestStrategy Agent API", "status": "running"}
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
