"""
Configuration Management
Handles .env read/write and settings persistence
"""

import os
from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from .env file."""
    
    # JIRA Configuration
    jira_base_url: str = Field(default="", alias="JIRA_BASE_URL")
    jira_email: str = Field(default="", alias="JIRA_EMAIL")
    jira_api_token: str = Field(default="", alias="JIRA_API_TOKEN")
    jira_acceptance_criteria_field: str = Field(default="customfield_10016", alias="JIRA_ACCEPTANCE_CRITERIA_FIELD")
    
    # Groq Configuration
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_default_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_DEFAULT_MODEL")
    
    # Ollama Configuration
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_default_model: str = Field(default="llama3.1", alias="OLLAMA_DEFAULT_MODEL")
    
    # LLM Settings
    default_provider: str = Field(default="groq", alias="DEFAULT_PROVIDER")
    llm_temperature: float = Field(default=0.3, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=8192, alias="LLM_MAX_TOKENS")
    
    # Template
    template_path: str = Field(default="./teststrategy.pdf", alias="TEMPLATE_PATH")
    
    # Export Settings
    company_name: str = Field(default="", alias="COMPANY_NAME")
    company_logo_path: str = Field(default="", alias="COMPANY_LOGO_PATH")
    default_classification: str = Field(default="Confidential", alias="DEFAULT_CLASSIFICATION")
    
    # Strategy Defaults
    default_depth: str = Field(default="detailed", alias="DEFAULT_DEPTH")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()


def update_env_file(updates: dict) -> bool:
    """
    Update the .env file with new values.
    Preserves existing values and comments.
    """
    env_path = Path(".env")
    
    # Read existing content
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    else:
        lines = []
    
    # Parse existing values
    existing = {}
    for i, line in enumerate(lines):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            existing[key] = (i, value)
    
    # Apply updates
    for key, value in updates.items():
        # Convert to env var format (uppercase with underscores)
        env_key = key.upper()
        
        if env_key in existing:
            # Update existing line
            line_num, _ = existing[env_key]
            lines[line_num] = f"{env_key}={value}\n"
        else:
            # Add new line
            lines.append(f"{env_key}={value}\n")
    
    # Write back
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    
    return True


def mask_sensitive(value: str, show_chars: int = 4) -> str:
    """Mask a sensitive value showing only first/last few chars."""
    if not value or len(value) <= show_chars * 2:
        return "***" if value else ""
    return f"{value[:show_chars]}...{value[-show_chars:]}"


def get_settings_for_frontend() -> dict:
    """Get settings safe to expose to frontend (no secrets)."""
    settings = get_settings()
    
    return {
        "jira_base_url": settings.jira_base_url,
        "jira_email": settings.jira_email,
        "jira_acceptance_criteria_field": settings.jira_acceptance_criteria_field,
        "groq_default_model": settings.groq_default_model,
        "ollama_base_url": settings.ollama_base_url,
        "ollama_default_model": settings.ollama_default_model,
        "default_provider": settings.default_provider,
        "llm_temperature": settings.llm_temperature,
        "llm_max_tokens": settings.llm_max_tokens,
        "template_path": settings.template_path,
        "company_name": settings.company_name,
        "default_classification": settings.default_classification,
        "default_depth": settings.default_depth,
        # Masked secrets
        "jira_api_token_set": bool(settings.jira_api_token),
        "jira_api_token_masked": mask_sensitive(settings.jira_api_token),
        "groq_api_key_set": bool(settings.groq_api_key),
        "groq_api_key_masked": mask_sensitive(settings.groq_api_key),
    }
