"""
Pydantic Request/Response Models
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class Provider(str, Enum):
    GROQ = "groq"
    OLLAMA = "ollama"


class Depth(str, Enum):
    STANDARD = "standard"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


class FocusArea(str, Enum):
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    SECURITY = "security"
    AUTOMATION = "automation"
    API = "api"
    ACCESSIBILITY = "accessibility"
    DISASTER_RECOVERY = "disaster_recovery"
    DATA_MIGRATION = "data_migration"
    MOBILE = "mobile"


# ==================== JIRA Models ====================

class JiraTicket(BaseModel):
    """Single JIRA ticket data."""
    key: str
    summary: str
    description: Optional[str] = None
    issue_type: str
    status: str
    priority: Optional[str] = None
    labels: List[str] = Field(default_factory=list)
    components: List[str] = Field(default_factory=list)
    acceptance_criteria: Optional[str] = None
    comments: List[Dict[str, str]] = Field(default_factory=list)
    linked_issues: List[Dict[str, str]] = Field(default_factory=list)
    subtasks: List[Dict[str, str]] = Field(default_factory=list)
    fix_versions: List[str] = Field(default_factory=list)
    sprint: Optional[str] = None
    url: Optional[str] = None


class JiraTicketRequest(BaseModel):
    """Request to fetch single ticket."""
    ticket_id: str
    fetch_children: bool = True


class JiraTicketsRequest(BaseModel):
    """Request to fetch multiple tickets."""
    ticket_ids: List[str]
    fetch_children: bool = True


class JiraFetchResponse(BaseModel):
    """Response from JIRA fetch."""
    success: bool
    tickets: List[JiraTicket] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    total_fetched: int = 0
    total_requested: int = 0


# ==================== Aggregated Context Models ====================

class ProjectSummary(BaseModel):
    """Summary of all tickets."""
    total_tickets: int
    epics: List[str]
    issue_type_breakdown: Dict[str, int]
    priority_breakdown: Dict[str, int]
    components: List[str]
    labels: List[str]


class FeatureArea(BaseModel):
    """Feature/epic area with related tickets."""
    epic_key: str
    epic_title: str
    description: Optional[str] = None
    priority: Optional[str] = None
    stories: List[Dict[str, Any]] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    risk_indicators: List[str] = Field(default_factory=list)


class AggregatedContext(BaseModel):
    """Full aggregated context for LLM."""
    project_summary: ProjectSummary
    feature_areas: List[FeatureArea]
    cross_cutting_concerns: List[str] = Field(default_factory=list)
    technical_context: Optional[str] = None
    all_comments_summary: Optional[str] = None


# ==================== Template Models ====================

class TemplateSection(BaseModel):
    """A section in the template."""
    number: str
    title: str
    depth: int
    subsections: List["TemplateSection"] = Field(default_factory=list)


class TemplateStructure(BaseModel):
    """Parsed template structure."""
    sections: List[TemplateSection]
    raw_text: str
    total_sections: int


class TemplatePreviewResponse(BaseModel):
    """Response for template preview."""
    success: bool
    structure: Optional[TemplateStructure] = None
    error: Optional[str] = None
    file_path: Optional[str] = None


# ==================== Generation Models ====================

class GenerateRequest(BaseModel):
    """Request to generate a test strategy."""
    jira_ticket_ids: List[str]
    fetch_children: bool = True
    additional_context: Optional[str] = None
    provider: Provider = Provider.GROQ
    model: str
    depth: Depth = Depth.DETAILED
    focus_areas: List[FocusArea] = Field(default_factory=lambda: [
        FocusArea.FUNCTIONAL,
        FocusArea.PERFORMANCE,
        FocusArea.SECURITY,
        FocusArea.AUTOMATION,
        FocusArea.API,
    ])
    temperature: float = Field(default=0.3, ge=0.0, le=1.0)


class SectionRegenerateRequest(BaseModel):
    """Request to regenerate a specific section."""
    section_number: str
    section_title: str
    previous_content: str  # All previously generated content for context
    jira_context: AggregatedContext
    provider: Provider
    model: str
    temperature: float = 0.3


class ExportRequest(BaseModel):
    """Request to export strategy."""
    content: str
    title: str
    project_name: Optional[str] = None
    classification: str = "Confidential"
    include_toc: bool = True


# ==================== SSE Stream Models ====================

class StreamEvent(BaseModel):
    """Base SSE event."""
    type: str


class StatusEvent(StreamEvent):
    """Status update event."""
    type: str = "status"
    stage: int
    message: str


class SectionStartEvent(StreamEvent):
    """Section generation start event."""
    type: str = "section_start"
    section: str
    section_number: Optional[str] = None


class ContentEvent(StreamEvent):
    """Content chunk event."""
    type: str = "content"
    text: str


class SectionCompleteEvent(StreamEvent):
    """Section generation complete event."""
    type: str = "section_complete"
    section: str


class DoneEvent(StreamEvent):
    """Generation complete event."""
    type: str = "done"
    total_tokens_used: Optional[int] = None
    generation_time_seconds: Optional[float] = None


class ErrorEvent(StreamEvent):
    """Error event."""
    type: str = "error"
    error: str
    code: Optional[str] = None


# ==================== History Models ====================

class StrategyHistoryItem(BaseModel):
    """History item for listing."""
    id: int
    title: str
    jira_ids: str
    project_name: Optional[str]
    provider: str
    model: str
    depth: str
    temperature: float
    created_at: str
    
    class Config:
        from_attributes = True


class StrategyHistoryList(BaseModel):
    """List of strategies with pagination."""
    items: List[StrategyHistoryItem]
    total: int
    skip: int
    limit: int


class StrategyDetail(BaseModel):
    """Full strategy details."""
    id: int
    title: str
    jira_ids: str
    project_name: Optional[str]
    provider: str
    model: str
    depth: str
    focus_areas: str
    temperature: float
    content: str
    template_structure: Optional[str]
    total_tokens_used: Optional[int]
    generation_time_seconds: Optional[float]
    created_at: str
    
    class Config:
        from_attributes = True


# ==================== Settings Models ====================

class SettingsResponse(BaseModel):
    """Settings response (safe for frontend)."""
    jira_base_url: str
    jira_email: str
    jira_acceptance_criteria_field: str
    jira_api_token_set: bool
    jira_api_token_masked: str
    
    groq_default_model: str
    groq_api_key_set: bool
    groq_api_key_masked: str
    
    ollama_base_url: str
    ollama_default_model: str
    
    default_provider: str
    llm_temperature: float
    llm_max_tokens: int
    
    template_path: str
    
    company_name: str
    default_classification: str
    
    default_depth: str


class SettingsUpdate(BaseModel):
    """Settings update request."""
    jira_base_url: Optional[str] = None
    jira_email: Optional[str] = None
    jira_api_token: Optional[str] = None
    jira_acceptance_criteria_field: Optional[str] = None
    
    groq_api_key: Optional[str] = None
    groq_default_model: Optional[str] = None
    
    ollama_base_url: Optional[str] = None
    ollama_default_model: Optional[str] = None
    
    default_provider: Optional[str] = None
    llm_temperature: Optional[float] = None
    llm_max_tokens: Optional[int] = None
    
    template_path: Optional[str] = None
    
    company_name: Optional[str] = None
    default_classification: Optional[str] = None
    
    default_depth: Optional[str] = None


# ==================== LLM Models ====================

class LLMTestRequest(BaseModel):
    """Request to test LLM connection."""
    provider: Provider
    model: Optional[str] = None


class LLMModelsResponse(BaseModel):
    """Response with available models."""
    provider: str
    models: List[str]
    default_model: str


class LLMProvidersResponse(BaseModel):
    """Response with provider status."""
    providers: List[Dict[str, Any]]
