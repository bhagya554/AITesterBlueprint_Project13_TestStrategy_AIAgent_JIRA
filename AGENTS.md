# AGENTS.md — TestStrategy Agent

> This file provides guidance to AI coding agents working on the TestStrategy Agent project. The reader is assumed to know nothing about the project beforehand.

---

## Project Overview

**TestStrategy Agent** is a production-grade, locally-hosted full-stack web application that automatically generates enterprise-level test strategy documents by pulling context from JIRA tickets and populating a PDF template using Large Language Models (LLM via Groq or Ollama).

### Key Distinction: Test Strategy vs Test Plan

A **Test Strategy** is a strategic, project-wide document covering:
- WHY we test (risk, business impact, compliance)
- WHAT types of testing are needed
- HOW testing will be organized (approach, levels, automation)
- WHO is responsible
- WHEN quality gates are enforced

This is **NOT** a test plan with individual test cases.

### Core Workflow

1. User provides JIRA ticket IDs (single Epic or multiple tickets)
2. Application fetches and aggregates JIRA context (descriptions, comments, linked issues)
3. PDF template is parsed to understand section structure
4. LLM generates strategic content section-by-section
5. Output is rendered in-browser with PDF/DOCX export options

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Backend** | Python 3.10+ / FastAPI | REST API, SSE streaming, static file serving |
| **Frontend** | React 18 (Vite) / Tailwind CSS | Modern SPA UI with HMR in dev |
| **Database** | SQLite via SQLAlchemy | Strategy history, settings persistence |
| **PDF Parsing** | pdfplumber | Extract template section structure |
| **PDF Export** | ReportLab | Professional PDF generation |
| **DOCX Export** | python-docx | Word document generation |
| **LLM** | Groq SDK + Ollama | Streaming inference with fallback options |
| **Config** | python-dotenv / Pydantic Settings | Environment-based configuration |

---

## Project Structure

```
Project13_TestStrategy_AI Agent_JIRA/
├── teststrategy-agent/              # Main application code
│   ├── backend/
│   │   ├── main.py                  # FastAPI entry point, CORS, static serving
│   │   ├── config.py                # Settings management (.env read/write)
│   │   ├── database.py              # SQLAlchemy models & SQLite session
│   │   ├── models.py                # Pydantic request/response models
│   │   ├── requirements.txt         # Python dependencies (15 packages)
│   │   ├── routers/                 # API route handlers (6 routers)
│   │   │   ├── __init__.py
│   │   │   ├── jira.py              # /api/jira/* endpoints
│   │   │   ├── generator.py         # /api/generate/* (SSE streaming)
│   │   │   ├── history.py           # /api/history/* CRUD
│   │   │   ├── settings.py          # /api/settings/*
│   │   │   ├── template.py          # /api/template/*
│   │   │   └── llm.py               # /api/llm/* (test, list models)
│   │   └── services/                # Business logic (7 services)
│   │       ├── __init__.py
│   │       ├── jira_client.py       # JIRA REST API + ADF parsing
│   │       ├── jira_aggregator.py   # Multi-ticket context aggregation
│   │       ├── template_parser.py   # PDF section extraction
│   │       ├── llm_provider.py      # Groq & Ollama abstraction
│   │       ├── prompt_builder.py    # LLM prompt construction
│   │       ├── context_optimizer.py # Token budget management
│   │       └── export_service.py    # PDF + DOCX generation
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── App.jsx              # Root component with sidebar navigation
│   │   │   ├── main.jsx             # React entry point
│   │   │   ├── index.css            # Tailwind imports + custom styles
│   │   │   ├── pages/               # Generator, History, Settings pages
│   │   │   │   ├── Generator.jsx    # Main generation interface
│   │   │   │   ├── History.jsx      # Saved strategies list
│   │   │   │   └── Settings.jsx     # Configuration UI
│   │   │   └── api/client.js        # Backend API wrappers (axios + fetch SSE)
│   │   ├── package.json             # npm dependencies
│   │   ├── vite.config.js           # Vite config with proxy
│   │   └── tailwind.config.js       # Custom color palette (navy + primary)
│   ├── .env                         # Configuration (secrets, API keys)
│   ├── .env.example                 # Template for .env
│   └── teststrategy.pdf             # Default 19-page template
├── tools/                           # Connectivity check scripts
│   ├── check_all.py                 # Master check runner
│   ├── check_jira.py                # JIRA API handshake
│   ├── check_groq.py                # Groq API handshake
│   ├── check_ollama.py              # Ollama API handshake
│   └── check_template.py            # PDF template parsing test
├── architecture/                    # Technical SOPs (Layer 1)
│   ├── SOP_jira_fetching.md
│   ├── SOP_template_parsing.md
│   ├── SOP_llm_generation.md
│   ├── SOP_context_optimization.md
│   └── SOP_export_formatting.md
├── .tmp/                            # Temporary files (ephemeral)
├── B.L.A.S.T.md                     # Master protocol documentation
├── CLAUDE.md                        # Quick reference for Claude Code
├── gemini.md                        # Project Constitution (schemas, rules, law)
├── findings.md                      # Research findings with code examples
├── task_plan.md                     # Phased implementation checklist
├── progress.md                      # Development log
├── TestStrategy_Agent_Prompt.md     # Full 762-line specification
├── teststrategy.pdf                 # Copy of default template
├── start.sh                         # Linux/Mac startup script
└── start.bat                        # Windows startup script
```

---

## Build and Run Commands

### Prerequisites

- Python 3.10+
- Node.js 18+
- Ollama (optional, for local LLM)

### Development Mode (Hot Reload)

```bash
# Terminal 1: Backend
cd teststrategy-agent/backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd teststrategy-agent/frontend
npm install
npm run dev
```

### Production Mode

```bash
# Linux/Mac
./start.sh

# Windows
start.bat
```

The production script:
1. Installs backend dependencies (`pip install`)
2. Builds frontend (`npm run build`)
3. Copies `dist/` to `backend/static/`
4. Starts uvicorn on port 8000

---

## Configuration

All configuration lives in `teststrategy-agent/.env`. Copy from `.env.example` and fill in your credentials:

```env
# JIRA Configuration (REQUIRED)
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token
JIRA_ACCEPTANCE_CRITERIA_FIELD=customfield_10016

# Groq Configuration (REQUIRED if using Groq)
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_DEFAULT_MODEL=llama-3.3-70b-versatile

# Ollama Configuration (REQUIRED if using Ollama)
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

## Code Style Guidelines

### Python (Backend)

1. **Type hints** — Use `typing` module for function signatures
2. **Docstrings** — All modules, classes, and functions have docstrings (Google style)
3. **Async/await** — All I/O operations (HTTP, DB) use async patterns
4. **Error handling** — Specific exceptions, never bare `except:`
5. **Naming** — `snake_case` for functions/variables, `PascalCase` for classes
6. **Imports** — Group: stdlib → third-party → local

Example:
```python
"""Module docstring."""
from typing import Optional, AsyncGenerator
import httpx

class MyService:
    """Class docstring."""
    
    async def fetch_data(self, url: str) -> dict:
        """Function docstring."""
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise MyServiceError(f"Failed to fetch: {e}")
```

### JavaScript/React (Frontend)

1. **Functional components** with hooks
2. **Naming** — `PascalCase` for components, `camelCase` for functions/variables
3. **Imports** — React → third-party → local components → local utils
4. **CSS** — Tailwind utility classes exclusively
5. **Props** — Destructure in component parameters

Example:
```jsx
import { useState, useEffect } from 'react'
import { Beaker } from 'lucide-react'
import { apiClient } from './api/client'

export default function MyComponent({ title }) {
  const [data, setData] = useState(null)
  
  useEffect(() => {
    loadData()
  }, [])
  
  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <h1 className="text-xl font-bold text-navy-900">{title}</h1>
    </div>
  )
}
```

---

## Testing Instructions

### Connectivity Tests

Run before full implementation to verify all external service handshakes:

```bash
# Test all connections
cd tools && python check_all.py

# Individual tests
python check_jira.py
python check_groq.py
python check_ollama.py
python check_template.py
```

### Manual Testing Checklist

1. **JIRA Fetch** — Single ticket, multiple tickets, child discovery
2. **Template Parse** — Section extraction, hierarchy building
3. **Generation** — Standard/Detailed/Comprehensive depths, all focus areas
4. **Export** — PDF and DOCX generation with proper formatting
5. **History** — Save, load, clone, delete strategies
6. **Settings** — Update and persist all configuration

---

## Security Considerations

1. **API Keys** — NEVER expose API keys to frontend. All LLM/JIRA calls go through backend only.

2. **Secrets Storage** — 
   - `.env` file for local development
   - Keys masked in settings API responses (`****` or `gsk_****Y3zQ`)
   - Use `get_settings_for_frontend()` to return safe subset

3. **CORS** — Configured for development:
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000

4. **Input Validation** — All API inputs validated via Pydantic models

5. **SQL Injection** — SQLAlchemy ORM used (parameterized queries)

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/jira/ticket/{id}` | Fetch single JIRA ticket |
| POST | `/api/jira/tickets` | Fetch multiple tickets |
| GET | `/api/jira/ticket/{id}/children` | Fetch child issues |
| GET | `/api/jira/test-connection` | Test JIRA credentials |
| POST | `/api/jira/aggregate` | Aggregate JIRA context |
| POST | `/api/generate/stream` | SSE stream generation |
| POST | `/api/generate/section` | Regenerate single section |
| POST | `/api/generate/export/pdf` | Export as PDF |
| POST | `/api/generate/export/docx` | Export as DOCX |
| GET | `/api/llm/providers` | List LLM providers |
| GET | `/api/llm/models/{provider}` | List available models |
| POST | `/api/llm/test` | Test LLM connection |
| GET | `/api/history` | List saved strategies |
| GET | `/api/history/{id}` | Get specific strategy |
| DELETE | `/api/history/{id}` | Delete strategy |
| POST | `/api/history/{id}/clone` | Clone strategy |
| GET | `/api/settings` | Get settings (masked) |
| PUT | `/api/settings` | Update settings |
| GET | `/api/settings/defaults` | Get default values |
| GET | `/api/template/preview` | Preview template structure |
| POST | `/api/template/upload` | Upload new template |
| GET | `/api/template/current` | Get current template info |

---

## Key Dependencies

### Backend
```
fastapi>=0.104.0          # Web framework
uvicorn[standard]>=0.24.0 # ASGI server
sqlalchemy>=2.0.0         # ORM
python-dotenv>=1.0.0      # Environment config
pydantic-settings>=2.1.0  # Settings management
httpx>=0.25.0             # HTTP client
pdfplumber>=0.10.0        # PDF parsing
reportlab>=4.0.0          # PDF generation
python-docx>=1.1.0        # DOCX generation
groq>=0.4.0               # Groq LLM SDK
ollama>=0.1.0             # Ollama LLM SDK
sse-starlette>=1.8.0      # SSE support
pydantic>=2.5.0           # Data validation
python-multipart>=0.0.6   # File uploads
aiofiles>=23.2.0          # Async file operations
```

### Frontend
```
react@^18.2.0             # UI framework
react-dom@^18.2.0         # DOM renderer
react-router-dom@^6.20.0  # Routing
axios@^1.6.0              # HTTP client
lucide-react@^0.294.0     # Icons
vite@^5.0.0               # Build tool
@vitejs/plugin-react@^4.2.0  # React plugin
tailwindcss@^3.3.6        # CSS framework
autoprefixer@^10.4.16     # CSS post-processing
postcss@^8.4.32           # CSS transformation
```

---

## Groq Model Registry

| Model ID | Context | Max Output | Use Case |
|----------|---------|------------|----------|
| `llama-3.3-70b-versatile` | 131K | 32K | Primary — best quality |
| `llama-3.1-8b-instant` | 131K | 131K | Fast — highest speed |
| `deepseek-r1-distill-llama-70b` | 131K | 16K | Reasoning — strategic analysis |
| `qwen-qwq-32b` | 131K | 16K | Alternative reasoning |
| `meta-llama/llama-4-scout-17b-16e-instruct` | 131K | 8K | Vision + multimodal |

**Note:** `mixtral-8x7b-32768` and `gemma-7b-it` are deprecated and removed from Groq.

---

## Template Structure

The default `teststrategy.pdf` has 19 pages with 13 major sections:

1. Introduction (1.1-1.4)
2. Project Overview (2.1-2.4)
3. Test Approach & Methodology (3.1-3.3)
4. Test Automation Strategy (4.1-4.4)
5. Test Environment Strategy (5.1-5.3)
6. Defect Management Strategy (6.1-6.4)
7. Risk-Based Testing & Risk Management (7.1-7.3)
8. Entry & Exit Criteria (8.1-8.2)
9. Test Metrics, KPIs & Reporting (9.1-9.3)
10. Roles and Responsibilities
11. Test Schedule & Milestones (11.1-11.2)
12. Communication & Escalation Plan (12.1-12.2)
13. Appendices (13.1-13.4)

---

## Critical Implementation Rules

1. **ADF Parsing is Mandatory** — JIRA Cloud descriptions are Atlassian Document Format JSON, not plain text. Use `adf_to_text()` in `jira_client.py`.

2. **Sectional Generation** — For Detailed/Comprehensive depth, generate section-by-section to avoid token limits. Feed previous sections as context.

3. **Context Optimization** — When 10+ JIRA tickets exceed model limits, truncate intelligently: comments first, then low-priority descriptions, keep titles/types always.

4. **Graceful Degradation** — If PDF template parsing fails, fall back to regex section numbering patterns.

5. **SSE Streaming** — Use `sse-starlette` with `EventSourceResponse` on backend. Frontend uses `fetch` + `ReadableStream` (not `EventSource`) for POST-based SSE.

6. **SQLite Auto-Create** — Database auto-creates on first run via `create_all()` at startup in `main.py` lifespan.

---

## Data Schemas

See `gemini.md` for complete schemas:

- **JIRA Ticket Input** — Parsed ticket with ADF-converted description
- **Aggregated Context** — Multi-ticket summary for LLM input
- **Template Output** — Section hierarchy from PDF parsing
- **Generation Request** — User parameters for generation
- **SSE Events** — Streaming response format

---

## Project Files Reference

| File | Purpose |
|------|---------|
| `gemini.md` | **Project Constitution** — schemas, rules, invariants. This is law. |
| `CLAUDE.md` | Quick reference for Claude Code (shortened version) |
| `B.L.A.S.T.md` | Master protocol documentation |
| `task_plan.md` | Phased implementation checklist |
| `findings.md` | Research findings with working code examples |
| `progress.md` | Development log — what was done, errors, next steps |
| `TestStrategy_Agent_Prompt.md` | Full 762-line specification (requirements source) |
| `teststrategy.pdf` | Default 19-page template |

---

## Maintenance

After any meaningful task:
1. Update `progress.md` with what happened and any errors
2. Store discoveries in `findings.md`
3. Update `gemini.md` ONLY when:
   - A schema changes
   - A rule is added
   - Architecture is modified

`gemini.md` is *law*.
The planning files are *memory*.
