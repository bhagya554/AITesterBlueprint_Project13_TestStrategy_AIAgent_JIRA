"""
Settings API Router
Endpoints for managing application settings
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from models import SettingsResponse, SettingsUpdate
from config import get_settings, get_settings_for_frontend, update_env_file, mask_sensitive

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings():
    """Get current settings (safe for frontend)."""
    return SettingsResponse(**get_settings_for_frontend())


@router.put("")
async def update_settings(update: SettingsUpdate):
    """Update application settings."""
    try:
        # Convert to dict, excluding None values
        updates = {k: v for k, v in update.model_dump().items() if v is not None}
        
        if not updates:
            return {"success": True, "message": "No changes to apply"}
        
        # Update .env file
        update_env_file(updates)
        
        return {
            "success": True,
            "message": "Settings updated successfully",
            "updated_fields": list(updates.keys())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


@router.get("/defaults")
async def get_default_settings():
    """Get default settings for new users."""
    return {
        "default_provider": "groq",
        "default_depth": "detailed",
        "default_temperature": 0.3,
        "default_max_tokens": 8192,
        "default_focus_areas": [
            "functional",
            "performance",
            "security",
            "automation",
            "api"
        ]
    }
