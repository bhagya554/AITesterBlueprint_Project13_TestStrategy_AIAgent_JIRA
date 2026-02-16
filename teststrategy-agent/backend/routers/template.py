"""
Template API Router
Endpoints for template preview and upload
"""

import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from models import TemplatePreviewResponse
from services.template_parser import parse_template, find_template_file
from config import get_settings

router = APIRouter(prefix="/api/template", tags=["template"])


@router.get("/preview", response_model=TemplatePreviewResponse)
async def preview_template():
    """Parse and return the current template structure."""
    try:
        template_path = find_template_file()
        
        if not template_path:
            return TemplatePreviewResponse(
                success=False,
                error="Template PDF not found",
                file_path=None
            )
        
        result = parse_template(template_path)
        
        return TemplatePreviewResponse(
            success=result.get("success", False),
            structure=result if result.get("success") else None,
            error=result.get("error"),
            file_path=template_path
        )
        
    except Exception as e:
        return TemplatePreviewResponse(
            success=False,
            error=str(e),
            file_path=None
        )


@router.post("/upload")
async def upload_template(file: UploadFile = File(...)):
    """Upload a new template PDF."""
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Save to project root as teststrategy.pdf
        file_path = Path("teststrategy.pdf")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Parse to verify it's valid
        result = parse_template(str(file_path))
        
        return {
            "success": True,
            "message": f"Template uploaded successfully: {file.filename}",
            "file_path": str(file_path.absolute()),
            "sections_found": result.get("total_sections", 0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload template: {str(e)}")
    finally:
        file.file.close()


@router.get("/current")
async def get_current_template():
    """Get information about the current template."""
    template_path = find_template_file()
    
    if not template_path:
        return {
            "found": False,
            "message": "No template found"
        }
    
    path = Path(template_path)
    
    return {
        "found": True,
        "file_path": str(path.absolute()),
        "file_name": path.name,
        "file_size": path.stat().st_size
    }
