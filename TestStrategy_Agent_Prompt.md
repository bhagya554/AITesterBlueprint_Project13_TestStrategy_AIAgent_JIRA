# Prompt: Build an Intelligent Test Strategy Generator Agent — Full-Stack Web Application

## Overview

Build a **production-grade, locally-hosted web application** called **"TestStrategy Agent"** that automatically generates comprehensive, enterprise-level test strategy documents by pulling context from JIRA tickets (epics, features, or project-level tickets) and populating a user-provided test strategy template using an LLM.

**Key difference from a Test Plan Agent**: A Test Strategy is a **higher-level, project-wide** document that defines the overall testing approach, methodology, tools, environments, risk management, and governance. It typically covers an entire project or release, whereas a Test Plan is per-feature/sprint. The AI must understand this distinction and generate strategic, architectural-level content — not just test cases.

The application must have a **clean, modern, professional UI**, run entirely on the user's local machine, and be launchable with a single command.

---

## Tech Stack (Mandatory)

| Layer        | Technology                                                              |
| ------------ | ----------------------------------------------------------------------- |
| **Backend**  | Python 3.10+ with **FastAPI**                                           |
| **Frontend** | **React 18** (Vite) with **Tailwind CSS**, served by the backend in prod|
| **Database** | **SQLite** (via SQLAlchemy) for history, settings & project persistence |
| **PDF Parse**| **pdfplumber** (for extracting template structure from test strategy PDF)|
| **PDF Gen**  | **ReportLab** or **WeasyPrint** (for exporting generated strategy as PDF)|
| **DOCX Gen** | **python-docx** (for exporting generated strategy as DOCX)             |
| **LLM**      | **Groq SDK** (`groq` Python package) AND **Ollama** (`ollama` package) |
| **Config**   | `.env` file via `python-dotenv`                                         |

---

## Application Pages & UI Design

### Page 1 — Home / Strategy Generator (Main Page)

This is the primary workspace. Layout (top to bottom):

1.  **Header Bar**
    - App logo/name **"TestStrategy Agent"** on the left (with a subtle strategy/chess icon)
    - Navigation links: **Generator** | **History** | **Settings**
    - LLM status indicator (green dot = connected, red = error) on the right
    - Small badge showing the connected JIRA instance URL

2.  **Configuration Strip** (horizontal bar below header)
    - **LLM Provider toggle**: Segmented control → `Groq` | `Ollama`
    - If Groq selected → show model dropdown (e.g., `llama-3.3-70b-versatile`, `mixtral-8x7b-32768`, `deepseek-r1-distill-llama-70b`)
    - If Ollama selected → show model dropdown auto-populated by calling `GET http://localhost:11434/api/tags` to list locally available models
    - **Connection test button** ("Test LLM") that makes a simple ping/completion call and shows ✅ or ❌

3.  **Input Section** — Two Input Modes (Tabs)

    **Tab A — Single JIRA Ticket (Epic/Feature)**
    - Large input field labeled **"JIRA Ticket ID (Epic / Feature / Story)"** with placeholder `e.g., VMO-1`
    - Checkbox: **"Also fetch all linked issues and subtasks for full context"** (checked by default)
    - Checkbox: **"Include child epics/stories context"** (for when the ticket is a high-level epic)

    **Tab B — Multiple JIRA Tickets (Project-Level Strategy)**
    - Multi-line input or tag-based input for **multiple JIRA IDs** (e.g., `VMO-1, VMO-2, VMO-15, VMO-42`)
    - Label: "Enter all related epics/features to generate a comprehensive project-wide test strategy"
    - Checkbox: **"Auto-discover linked issues across all tickets"**

    **Common elements below both tabs:**
    - **"Additional Context"** expandable text area — for user to add project-specific context like tech stack, compliance requirements, team structure, deployment model, etc.
    - **"Fetch & Generate"** primary button (prominent, colored)
    - **"Fetch Only"** secondary button (outline style — fetches JIRA data and displays it for review before generation)

4.  **Context Preview Panel** (collapsible, appears after fetch)
    - Shows extracted JIRA data in organized, expandable cards:
      - **Project Summary Card**: Aggregated view — total tickets fetched, issue types breakdown, priorities distribution
      - **Per-Ticket Cards** (collapsed by default, expandable):
        - Title, Status, Type, Priority, Labels, Components
        - Description (rendered markdown)
        - Acceptance Criteria
        - Linked Issues (with summaries)
        - Subtasks (with statuses)
        - Comments (last 5 per ticket, collapsed)
    - **"Edit Context"** button to add/modify/remove extracted content before generation
    - **Context token count** indicator (shows approximate token usage to help user understand LLM context limits)

5.  **Generation Controls** (appears after fetch, before generation)
    - **Strategy Depth selector**: `Standard` | `Detailed` | `Comprehensive`
      - Standard: Fills all template sections with moderate detail (~3,000-5,000 words)
      - Detailed: Thorough content with examples and specifics (~5,000-8,000 words)
      - Comprehensive: Maximum detail, includes worked examples, sample test cases in appendix (~8,000-12,000 words)
    - **Focus Areas** (multi-select checkboxes):
      - ☑ Functional Testing Strategy
      - ☑ Performance Testing Strategy
      - ☑ Security Testing Strategy
      - ☑ Automation Strategy
      - ☑ API Testing Strategy
      - ☐ Accessibility Testing
      - ☐ Disaster Recovery Testing
      - ☐ Data Migration Testing
      - ☐ Mobile Testing
    - **Temperature slider** (0.0 – 1.0, default 0.3)

6.  **Generation Output Panel**
    - While generating: show a **streaming text output** area with a typing indicator and **progress stages**:
      - Stage 1: "Analyzing JIRA context..." (with checkmark when done)
      - Stage 2: "Parsing template structure..." (with checkmark)
      - Stage 3: "Generating test strategy..." (active, with streaming text)
      - Stage 4: "Finalizing document..." (with checkmark)
    - After generation completes:
      - Rendered output in a **document-style view** (white card with shadow, proper heading hierarchy, formatted tables, styled sections)
      - **Collapsible table of contents** sidebar (auto-generated from section headings)
      - **Action buttons row**:
        - 📋 **Copy to Clipboard** (copies full markdown)
        - 📄 **Download as PDF** (professionally formatted with cover page, TOC, headers/footers)
        - 📝 **Download as DOCX** (with proper heading styles, tables, formatting)
        - 🔄 **Regenerate** (re-runs with same context)
        - ✏️ **Regenerate Section** (dropdown to pick a specific section to regenerate)
        - 💾 **Save to History**

---

### Page 2 — History

- Table/list of previously generated test strategies with columns:
  - Project / JIRA IDs | Strategy Title | LLM Used | Model | Depth | Generated Date | Actions
- Actions: **View** (opens in full document view), **Download PDF**, **Download DOCX**, **Clone & Edit** (loads into generator with same settings), **Delete**
- Search/filter bar with filters for date range, LLM provider, and project
- **Compare** feature: Select two strategies and view them side-by-side (useful for version comparison)
- Data stored in local SQLite database

---

### Page 3 — Settings

Organized in clearly labeled sections with cards:

**JIRA Configuration**
- JIRA Base URL (e.g., `https://mycompany.atlassian.net`)
- JIRA User Email
- JIRA API Token (masked password field with show/hide toggle)
- **"Test JIRA Connection"** button → makes a `/rest/api/3/myself` call, shows ✅ with user display name or ❌ with error
- Custom field mapping (optional): Allow user to specify which custom field contains "Acceptance Criteria" (defaults to `customfield_10016`)

**Groq Configuration**
- Groq API Key (masked password field with show/hide toggle)
- Preferred Default Model (dropdown)
- **"Test Groq Connection"** button

**Ollama Configuration**
- Ollama Base URL (default: `http://localhost:11434`)
- **"Test Ollama Connection"** button → fetches available models and displays them
- Preferred Default Model (dropdown, populated after successful connection test)

**Template Configuration**
- Show current template file path (default: `./teststrategy.pdf` or configurable)
- **"Upload New Template"** — file upload for PDF template
- **"Preview Template Structure"** button → extracts and displays the parsed section headings from the PDF so the user can verify parsing is correct
- **"Reset to Default Template"** button

**Generation Defaults**
- Default strategy depth (Standard / Detailed / Comprehensive)
- Default temperature (slider 0.0 – 1.0)
- Default max tokens (slider 2000 – 16000, default 8192)
- Default focus areas (checkboxes)

**Export Settings**
- Company name (appears on PDF cover page)
- Company logo upload (optional, for PDF header)
- Default classification level (Confidential / Internal / Public)

All settings saved to `.env` file AND SQLite (so they persist across restarts).

---

## Backend Architecture — Detailed Specifications

### Project Structure

```
teststrategy-agent/
├── backend/
│   ├── main.py                  # FastAPI app entry point, CORS, static file serving
│   ├── config.py                # Settings management (.env read/write)
│   ├── database.py              # SQLAlchemy models & session (SQLite)
│   ├── models.py                # Pydantic request/response models
│   ├── routers/
│   │   ├── jira.py              # /api/jira/* endpoints
│   │   ├── generator.py         # /api/generate/* endpoints (SSE streaming)
│   │   ├── history.py           # /api/history/* CRUD endpoints
│   │   ├── settings.py          # /api/settings/* endpoints
│   │   ├── template.py          # /api/template/* endpoints
│   │   └── llm.py               # /api/llm/* endpoints (test connections, list models)
│   ├── services/
│   │   ├── jira_client.py       # JIRA REST API integration (single + multi-ticket)
│   │   ├── jira_aggregator.py   # Aggregates context from multiple JIRA tickets
│   │   ├── template_parser.py   # PDF template extraction logic
│   │   ├── llm_provider.py      # Abstraction layer over Groq & Ollama
│   │   ├── prompt_builder.py    # Constructs the LLM prompt (the core intelligence)
│   │   ├── context_optimizer.py # Manages token budget, truncates intelligently
│   │   └── export_service.py    # PDF and DOCX generation from output
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── Generator.jsx     # Main strategy generator page
│   │   │   ├── History.jsx       # Saved strategies list
│   │   │   └── Settings.jsx      # Configuration page
│   │   ├── components/
│   │   │   ├── Header.jsx
│   │   │   ├── JiraInput.jsx     # Single + multi ticket input tabs
│   │   │   ├── JiraPreview.jsx   # Context preview cards
│   │   │   ├── GenerationControls.jsx  # Depth, focus areas, temperature
│   │   │   ├── StreamOutput.jsx  # Streaming output with progress stages
│   │   │   ├── DocumentView.jsx  # Rendered document with TOC sidebar
│   │   │   ├── LLMSelector.jsx   # Provider + model selection
│   │   │   └── ExportButtons.jsx # Copy, PDF, DOCX, Regenerate actions
│   │   └── api/
│   │       └── client.js        # Axios/fetch wrappers for backend API
│   ├── package.json
│   └── vite.config.js
├── .env                          # All secrets and configuration
├── teststrategy.pdf              # Default template (the one provided by user)
├── start.sh                      # Single-command launcher (Linux/Mac)
├── start.bat                     # Single-command launcher (Windows)
└── README.md                     # Full setup and usage instructions
```

### API Endpoints

| Method | Endpoint                              | Description                                                      |
| ------ | ------------------------------------- | ---------------------------------------------------------------- |
| GET    | `/api/jira/ticket/{id}`               | Fetch and parse a single JIRA ticket by ID                       |
| POST   | `/api/jira/tickets`                   | Fetch multiple JIRA tickets (body: list of IDs)                  |
| GET    | `/api/jira/ticket/{id}/children`      | Fetch all subtasks + linked issues of a ticket                   |
| GET    | `/api/jira/test-connection`           | Test JIRA credentials                                            |
| POST   | `/api/generate/stream`                | SSE endpoint — streams generated test strategy                   |
| POST   | `/api/generate/section`               | Regenerate a specific section only                               |
| POST   | `/api/generate/export/pdf`            | Generate and return strategy as formatted PDF                    |
| POST   | `/api/generate/export/docx`           | Generate and return strategy as formatted DOCX                   |
| GET    | `/api/llm/providers`                  | List available providers and their connection status              |
| GET    | `/api/llm/models/{provider}`          | List models for a provider                                       |
| POST   | `/api/llm/test`                       | Test LLM connection with a simple prompt                         |
| GET    | `/api/history`                        | List all saved test strategies (with pagination + search)        |
| GET    | `/api/history/{id}`                   | Get a specific saved strategy                                    |
| DELETE | `/api/history/{id}`                   | Delete a saved strategy                                          |
| POST   | `/api/history/{id}/clone`             | Clone a saved strategy's settings for re-generation              |
| GET    | `/api/settings`                       | Get current settings (API keys masked)                           |
| PUT    | `/api/settings`                       | Update settings                                                  |
| GET    | `/api/template/preview`               | Parse and return template structure                              |
| POST   | `/api/template/upload`                | Upload a new template PDF                                        |

---

### JIRA Client (`jira_client.py`) — Detailed Logic

```python
# Connection: Use requests/httpx with Basic Auth
# Auth: base64(email:api_token) in Authorization header
# Base endpoint: {JIRA_BASE_URL}/rest/api/3/issue/{ticket_id}
#
# === SINGLE TICKET FETCH ===
# Fields to extract:
#   - fields.summary → Title
#   - fields.description → Description (ADF JSON → convert to plain text)
#   - fields.issuetype.name → Issue Type (Epic, Story, Task, Bug, etc.)
#   - fields.status.name → Status
#   - fields.priority.name → Priority
#   - fields.labels → Labels
#   - fields.components → Components
#   - fields.comment.comments → Comments (body text, author, date)
#   - fields.issuelinks → Linked Issues (type, inward/outward issue key + summary)
#   - fields.subtasks → Subtasks (key + summary + status)
#   - fields.attachment → Attachments (filename, mimeType only)
#   - fields.customfield_* → Acceptance Criteria (commonly customfield_10016)
#   - fields.fixVersions → Fix Versions / Release info
#   - fields.sprint → Sprint info (if applicable)
#
# === MULTI-TICKET FETCH ===
# For project-wide strategy, fetch multiple tickets efficiently:
#   - Use JQL search: /rest/api/3/search?jql=key in (VMO-1, VMO-2, ...)
#   - Or: /rest/api/3/search?jql=project=VMO AND issuetype=Epic
#   - Batch fetch with pagination (maxResults=50 per page)
#
# === CHILD TICKET DISCOVERY ===
# When "fetch children" is enabled:
#   - For Epics: Use /rest/api/3/search?jql="Epic Link"=VMO-1
#   - For Stories with subtasks: Already in fields.subtasks
#   - For linked issues: Recursively fetch 1 level deep
#   - Aggregate all context into a structured summary
#
# IMPORTANT: Handle Atlassian Document Format (ADF) → convert nested JSON to plain text
# IMPORTANT: Handle both Jira Cloud and Jira Server API differences
# IMPORTANT: Respect rate limits — add retry with exponential backoff
```

### JIRA Aggregator (`jira_aggregator.py`) — Critical for Strategy

```python
# This service takes raw data from multiple JIRA tickets and produces
# a structured, aggregated context suitable for strategy generation.
#
# Output structure:
# {
#   "project_summary": {
#     "total_tickets": 15,
#     "epics": ["VMO-1: User Auth", "VMO-2: Payment System"],
#     "issue_type_breakdown": {"Epic": 3, "Story": 8, "Task": 4},
#     "priority_breakdown": {"Critical": 2, "High": 5, "Medium": 6, "Low": 2},
#     "components": ["Backend", "Frontend", "Mobile", "Infrastructure"],
#     "labels": ["security", "performance", "MVP"],
#   },
#   "feature_areas": [
#     {
#       "epic": "VMO-1: User Authentication & Authorization",
#       "description": "...",
#       "stories": [...],
#       "acceptance_criteria": [...],
#       "risk_indicators": ["security", "third-party integration"],
#     },
#     ...
#   ],
#   "cross_cutting_concerns": ["Performance requirements mentioned in X tickets",
#                               "Security compliance noted in Y tickets"],
#   "technical_context": "Extracted tech stack, integrations, architecture hints",
#   "all_comments_summary": "Key discussion points from comments",
# }
```

---

### Template Parser (`template_parser.py`) — Detailed Logic

```python
# Use pdfplumber to open the test strategy template PDF
# Extract all text from all pages
# Identify section headings by analyzing:
#   - Font size changes (larger = heading)
#   - Bold text patterns
#   - Numbering patterns (1., 1.1, 1.1.1, 2., etc.)
#   - Known test strategy sections:
#     * Document Control, Introduction, Purpose, Scope, Objectives
#     * Project Overview, Architecture, Stakeholders
#     * Test Approach & Methodology, Testing Levels, Testing Types
#     * Test Automation Strategy, Framework, CI/CD
#     * Test Environment Strategy, Test Data Management
#     * Defect Management, Severity, SLA
#     * Risk Management, Risk Register, Prioritization
#     * Entry & Exit Criteria, Quality Gates
#     * Metrics, KPIs, Reporting
#     * Roles & Responsibilities, RACI
#     * Schedule & Milestones
#     * Communication & Escalation Plan
#     * Appendices, Glossary, Assumptions, Constraints
#
# Output: structured dict with section hierarchy
# {
#   "sections": [
#     {
#       "number": "1",
#       "title": "Introduction",
#       "subsections": [
#         {"number": "1.1", "title": "Purpose", "subsections": []},
#         {"number": "1.2", "title": "Scope", "subsections": []},
#       ]
#     },
#     ...
#   ],
#   "raw_text": "full extracted text for fallback context"
# }
#
# If PDF parsing fails, fall back to raw text and let the LLM interpret structure
```

---

### LLM Provider (`llm_provider.py`) — Detailed Logic

```python
# Abstract base interface:
# class LLMProvider:
#     async def generate_stream(prompt: str, system_prompt: str, model: str,
#                                temperature: float, max_tokens: int) → AsyncGenerator[str]
#     async def test_connection() → bool
#     async def list_models() → List[str]
#
# GroqProvider:
#   - Uses `groq` Python SDK
#   - Streaming via client.chat.completions.create(stream=True)
#   - Available models: llama-3.3-70b-versatile, mixtral-8x7b-32768,
#     gemma2-9b-it, llama-3.1-8b-instant, deepseek-r1-distill-llama-70b
#   - Error handling: rate limits (retry with exponential backoff, show
#     countdown in UI), auth errors, model not found, context length exceeded
#   - For "Comprehensive" depth: may need to split generation into multiple
#     calls (section by section) if output exceeds model's max output tokens
#
# OllamaProvider:
#   - Uses `ollama` Python package or direct HTTP to localhost:11434
#   - Streaming via /api/chat endpoint with stream=true
#   - List models via /api/tags
#   - Error handling: connection refused (Ollama not running),
#     model not pulled, out of memory
#   - Better suited for "Standard" depth; warn user about limitations
#     for "Comprehensive" with smaller models
#
# Factory function: get_provider(provider_name: str) → LLMProvider
#
# CRITICAL for Test Strategy: The output will be MUCH longer than a test plan.
# Implement a "sectional generation" mode where the strategy is generated
# section by section, each section fed the previous sections as context.
# This avoids hitting output token limits and allows per-section regeneration.
```

---

### Context Optimizer (`context_optimizer.py`) — Token Management

```python
# Test strategies require MORE context than test plans because they span
# multiple features/epics. This service manages the token budget.
#
# Strategy:
# 1. Calculate available context window (model-specific)
#    - Reserve ~2000 tokens for system prompt
#    - Reserve ~1500 tokens for template structure
#    - Reserve output tokens (based on depth: 4K/8K/12K)
#    - Remaining = available for JIRA context
#
# 2. If JIRA context exceeds budget, truncate in priority order:
#    - KEEP: All ticket titles, types, priorities, components (always)
#    - KEEP: Descriptions of top-priority tickets (always)
#    - TRIM: Comments → summarize instead of full text
#    - TRIM: Lower-priority ticket descriptions → summarize
#    - TRIM: Linked issue details → just IDs and titles
#    - DROP: Attachment metadata (least useful for strategy)
#
# 3. Provide a "context utilization" metric to the frontend
#    so user can see how much of the context window is being used
```

---

### Prompt Builder (`prompt_builder.py`) — The Core Intelligence

This is the **most critical component**. The prompt must guide the LLM to think strategically, not just list test cases.

```
SYSTEM PROMPT:
You are a Principal QA Architect and Test Strategist with 20+ years of experience in enterprise
software quality assurance across industries including fintech, healthcare, e-commerce, and SaaS.
You specialize in creating comprehensive test strategy documents that align testing efforts with
business objectives, manage risk, and optimize quality investment.

Your task is to generate a detailed, enterprise-grade Test Strategy document based on:
1. The provided template structure (which you MUST follow exactly)
2. The JIRA project context (tickets, epics, features, requirements)
3. Any additional context provided by the user

CRITICAL GUIDELINES:
1. A Test Strategy is a STRATEGIC document, not a test plan. Focus on:
   - WHY we test (risk, business impact, compliance)
   - WHAT types of testing are needed and their relative priority
   - HOW testing will be organized (approach, levels, automation strategy)
   - WHO is responsible for what
   - WHEN quality gates are enforced
   - Do NOT list individual test cases — that belongs in test plans

2. Fill EVERY section of the template with substantive, project-specific content.
   Never leave a section with just placeholder text or generic boilerplate.

3. Derive specific recommendations from the JIRA context:
   - If tickets mention "API" → include API testing strategy
   - If tickets mention "payment" or "PII" → emphasize security testing
   - If components include "Mobile" → include mobile testing strategy
   - If labels include "performance" → detail performance testing approach
   - Analyze priorities to determine risk-based testing allocation

4. Include concrete, actionable content:
   - Specific tool recommendations (based on implied tech stack)
   - Realistic coverage targets with justification
   - Specific metrics with target values
   - Realistic risk items with mitigations (not generic risks)

5. Use professional QA terminology and maintain executive-level readability.

6. Maintain internal consistency — if you mention a tool in Section 4,
   reference it again in Section 5 (environments) and Section 9 (reporting).

7. Format output in clean Markdown with proper heading hierarchy matching the template.
   Use tables where the template uses tables. Use bullet points sparingly and meaningfully.

{depth_instruction}

---
DEPTH INSTRUCTIONS (injected based on user selection):

Standard:
"Generate a focused test strategy covering all template sections with moderate detail.
 Each major section should be 200-400 words. Total output: ~3,000-5,000 words."

Detailed:
"Generate a thorough test strategy with specific examples and detailed recommendations.
 Each major section should be 400-700 words. Include specific tool configurations,
 sample metrics calculations, and detailed risk analysis. Total output: ~5,000-8,000 words."

Comprehensive:
"Generate an exhaustive test strategy suitable for enterprise governance review.
 Each major section should be 600-1000 words. Include worked examples, sample
 test case outlines for critical areas, detailed RACI matrix, specific SLA
 calculations, tool comparison rationale, and appendices with supporting detail.
 Total output: ~8,000-12,000 words."

---
USER PROMPT:

## TEST STRATEGY TEMPLATE STRUCTURE
{extracted_template_sections_with_full_hierarchy}

## JIRA PROJECT CONTEXT

### Project Summary
- Total Tickets Analyzed: {total_tickets}
- Epics: {epic_list_with_titles}
- Issue Types: {type_breakdown}
- Priority Distribution: {priority_breakdown}
- Components: {component_list}
- Labels: {label_list}
- Fix Versions / Releases: {version_info}

### Feature Areas
{for each epic/feature area:}
#### {epic_key}: {epic_title}
- **Type**: {issue_type}
- **Priority**: {priority}
- **Description**: {description}
- **Acceptance Criteria**: {acceptance_criteria}
- **Stories/Subtasks**:
  {list of child tickets with summaries and priorities}
- **Linked Issues**: {linked issues}

### Cross-Cutting Concerns Identified
{aggregated patterns: security mentions, performance requirements, compliance needs, etc.}

### Technical Context Signals
{extracted tech stack hints, integration points, architecture patterns from descriptions}

### Key Discussion Points (from Comments)
{summarized important points from ticket comments}

{additional_user_context if provided}

### User-Selected Focus Areas
{list of checked focus areas: Functional, Performance, Security, Automation, etc.}

---
Generate the complete Test Strategy document now, following the template structure exactly.
Ensure every section is populated with project-specific, actionable content derived from
the JIRA context above. Do not include placeholder text like "[fill in]" — instead, make
informed recommendations based on the available context and note your assumptions.
```

---

### Export Service (`export_service.py`)

**PDF Export** — Use ReportLab or WeasyPrint to create a professional document:
- **Cover page**: Project name, "Test Strategy Document", version, date, classification, company logo (if configured)
- **Document control page**: Revision history table, reviewers/approvers table
- **Table of Contents**: Auto-generated from headings
- **Content pages**: Proper heading styles (H1/H2/H3), formatted tables with colored headers, styled bullet points, risk matrix with color coding
- **Headers**: "Test Strategy Document | [Project Name]" with page border
- **Footers**: "Confidential | Page X of Y"

**DOCX Export** — Use python-docx:
- Title page with full formatting
- Heading styles (Heading 1, 2, 3) matching template hierarchy
- Tables with header row shading and borders
- Professional paragraph spacing and fonts
- Exportable TOC field (user updates in Word)
- Company logo in header (if configured)

---

## Streaming & Sectional Generation

The generation endpoint MUST use **Server-Sent Events (SSE)** for real-time streaming.

For **"Comprehensive"** depth or when generating from many JIRA tickets, implement **sectional generation**:

```python
# Sectional generation approach:
# 1. Parse template into sections
# 2. For each major section (1-13):
#    a. Build a section-specific prompt that includes:
#       - The overall template structure (for context)
#       - Previously generated sections (for consistency)
#       - The current section to generate
#       - Relevant JIRA context for this section
#    b. Stream the output for this section
#    c. Store the generated section
#    d. Send a "section_complete" SSE event
# 3. After all sections, send "done" event

# This approach:
# - Avoids hitting output token limits
# - Enables per-section regeneration
# - Maintains consistency across sections
# - Gives the user visible progress
```

**Backend SSE Events:**
```python
{"type": "status", "stage": 1, "message": "Analyzing JIRA context (15 tickets)..."}
{"type": "status", "stage": 2, "message": "Parsing template structure (13 sections found)..."}
{"type": "section_start", "section": "1. Introduction"}
{"type": "content", "text": "chunk of generated text..."}
{"type": "section_complete", "section": "1. Introduction"}
{"type": "section_start", "section": "2. Project Overview"}
{"type": "content", "text": "chunk of generated text..."}
...
{"type": "done", "total_tokens_used": 15420, "generation_time_seconds": 45}
```

---

## Error Handling Requirements

| Error Scenario                           | User-Facing Message                                                                  |
| ---------------------------------------- | ------------------------------------------------------------------------------------ |
| JIRA auth failure (401)                  | "JIRA authentication failed. Check your email and API token in Settings."            |
| JIRA ticket not found (404)              | "Ticket {ID} not found. Verify the ticket ID and your JIRA project access."         |
| JIRA connection refused                  | "Cannot reach JIRA server at {URL}. Check the URL in Settings."                     |
| Multiple JIRA IDs — partial failure      | "Successfully fetched 12/15 tickets. Failed: VMO-99 (not found), VMO-50 (no access), VMO-77 (not found). Proceed with available data?" |
| Groq auth failure                        | "Groq API key is invalid. Update it in Settings."                                   |
| Groq rate limit                          | "Groq rate limit reached. Retrying in {n} seconds... ({attempt}/3)"                 |
| Groq context length exceeded             | "Context too large for selected model. Switching to sectional generation mode..."    |
| Ollama not running                       | "Cannot connect to Ollama at {URL}. Start it with: `ollama serve`"                  |
| Ollama model not found                   | "Model '{name}' not available. Pull it first: `ollama pull {name}`"                 |
| Ollama out of memory                     | "Model requires more memory than available. Try a smaller model or reduce context."  |
| Template PDF not found                   | "Test strategy template not found at {path}. Upload one in Settings."               |
| Template parsing produced no sections    | "Could not identify sections in template. Using raw text as reference."              |
| Generation timeout (>5 min per section)  | "Generation timed out. Try a simpler model or reduce strategy depth."               |

---

## Single-Command Startup

**`start.sh`** (Linux/Mac):
```bash
#!/bin/bash
set -e
echo "🚀 Starting TestStrategy Agent..."

# Check Python version
python3 --version || { echo "❌ Python 3.10+ required"; exit 1; }

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd backend
pip install -r requirements.txt --quiet

# Install frontend dependencies & build
echo "📦 Building frontend..."
cd ../frontend
npm install --silent
npm run build

# Copy build to backend static folder
rm -rf ../backend/static
cp -r dist ../backend/static

# Start the server
cd ../backend
echo ""
echo "✅ TestStrategy Agent is running!"
echo "🌐 Open http://localhost:8000 in your browser"
echo ""
uvicorn main:app --host 0.0.0.0 --port 8000
```

**`start-dev.sh`** (for development with hot reload):
```bash
#!/bin/bash
echo "🔧 Starting TestStrategy Agent in development mode..."
# Terminal 1: Backend with auto-reload
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
# Terminal 2: Frontend dev server with HMR
cd frontend && npm run dev &
wait
```

---

## `.env` File Structure

```env
# JIRA Configuration
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token
JIRA_ACCEPTANCE_CRITERIA_FIELD=customfield_10016

# Groq Configuration
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_DEFAULT_MODEL=llama-3.3-70b-versatile

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3.1

# LLM Settings
DEFAULT_PROVIDER=groq
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=8192

# Template
TEMPLATE_PATH=./teststrategy.pdf

# Export Settings
COMPANY_NAME=
COMPANY_LOGO_PATH=
DEFAULT_CLASSIFICATION=Confidential

# Strategy Defaults
DEFAULT_DEPTH=detailed
```

---

## UI Design Guidelines

- **Color scheme**: Professional corporate — dark navy sidebar (#1B3A5C) with white content area. Primary accent: corporate blue (#2E75B6). Success green, warning amber, error red for status indicators.
- **Typography**: Inter (or system sans-serif), 14px base, proper heading hierarchy (24/20/16px)
- **Layout**: Fixed sidebar navigation + scrollable main content area
- **Document output panel**: White card with subtle shadow, 720px max-width centered, proper typographic hierarchy — should look like a real document preview
- **TOC sidebar**: Collapsible right panel with clickable section links that scroll to that section
- **Loading states**: Multi-stage progress indicator with checkmarks, skeleton loaders for JIRA fetch
- **Toast notifications**: For success/error messages
- **Responsive**: Optimized for 1024px+ screens
- **Dark mode**: Optional toggle in header

---

## README.md Must Include

1. Project title, tagline, and one-line description
2. Screenshot/GIF of the running application (placeholder instructions)
3. Feature highlights (bullet list)
4. Prerequisites: Python 3.10+, Node.js 18+, Ollama (optional)
5. Quick start: Clone → Configure `.env` → Run `./start.sh` → Open browser
6. How to get a JIRA API token (with link to Atlassian docs)
7. How to get a Groq API key (with link to Groq console)
8. How to set up Ollama: Install → `ollama pull llama3.1` → `ollama serve`
9. Using the application (brief walkthrough)
10. Troubleshooting section for common errors
11. License

---

## Critical Implementation Notes

1. **NEVER expose API keys to the frontend** — all LLM and JIRA calls go through the backend only
2. **JIRA ADF (Atlassian Document Format) parsing is critical** — Jira Cloud description fields are complex nested JSON, NOT plain text. You MUST implement a proper ADF-to-text converter
3. **Sectional generation is essential** — Test strategies are long documents (5,000-12,000 words). Most LLMs have output token limits of 4K-8K. You MUST implement section-by-section generation for "Detailed" and "Comprehensive" modes
4. **Context window management** — When fetching 10+ JIRA tickets, the combined context can easily exceed model limits. The context optimizer MUST intelligently truncate while preserving the most important information
5. **Template parser must be robust** — If PDF formatting analysis fails, fall back to regex patterns for section numbering (1., 1.1, 2., etc.) and common section names
6. **SQLite DB must auto-create on first run** — use `create_all()` at startup, no manual migration needed
7. **CORS must be configured** for development (frontend port 5173, backend port 8000)
8. **The test strategy template PDF** (provided by the user) should be placed in the project root as `teststrategy.pdf`. The application should detect it on startup and show a warning if not found
9. **Maintain section cross-references** — When generating section by section, feed previously generated sections as context so the LLM can reference tools/processes mentioned earlier
10. **Rate limit awareness** — Groq has aggressive rate limits on free tier. Implement exponential backoff with user-visible countdown timer
