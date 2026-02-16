# Project Constitution — TestStrategy Agent

> This file is **law**. All schemas, rules, and architectural decisions live here.

---

## Discovery Answers

| Question | Answer |
|---|---|
| **North Star** | Build a production-grade, locally-hosted web app ("TestStrategy Agent") that auto-generates enterprise-level test strategy documents by pulling context from JIRA tickets and populating a user-provided PDF template using an LLM |
| **Integrations** | JIRA Cloud REST API (Basic Auth), Groq SDK (LLM), Ollama (local LLM), pdfplumber (PDF parsing), ReportLab/WeasyPrint (PDF export), python-docx (DOCX export) |
| **Source of Truth** | JIRA tickets (epics, features, stories) + user-provided test strategy PDF template (`teststrategy.pdf`) |
| **Delivery Payload** | Rendered document in web UI + PDF export + DOCX export + saved to local SQLite history |
| **Behavioral Rules** | Generate STRATEGIC content (not test cases), fill every template section with project-specific content, derive recommendations from JIRA context signals, use professional QA terminology, maintain cross-section consistency |

---

## Tech Stack (Mandatory)

| Layer | Technology |
|---|---|
| Backend | Python 3.10+ with FastAPI |
| Frontend | React 18 (Vite) with Tailwind CSS |
| Database | SQLite via SQLAlchemy |
| PDF Parse | pdfplumber |
| PDF Gen | ReportLab or WeasyPrint |
| DOCX Gen | python-docx |
| LLM | Groq SDK + Ollama |
| Config | `.env` via python-dotenv |

---

## Data Schemas

### JIRA Ticket Input (per ticket)
```json
{
  "key": "VMO-1",
  "summary": "string",
  "description": "string (converted from ADF JSON)",
  "issue_type": "Epic | Story | Task | Bug",
  "status": "string",
  "priority": "Critical | High | Medium | Low",
  "labels": ["string"],
  "components": ["string"],
  "acceptance_criteria": "string (from customfield_10016)",
  "comments": [{"body": "string", "author": "string", "date": "string"}],
  "linked_issues": [{"type": "string", "key": "string", "summary": "string"}],
  "subtasks": [{"key": "string", "summary": "string", "status": "string"}],
  "fix_versions": ["string"],
  "sprint": "string | null"
}
```

### Aggregated JIRA Context (fed to LLM)
```json
{
  "project_summary": {
    "total_tickets": "int",
    "epics": ["KEY: Title"],
    "issue_type_breakdown": {"Epic": "int", "Story": "int", "Task": "int"},
    "priority_breakdown": {"Critical": "int", "High": "int", "Medium": "int", "Low": "int"},
    "components": ["string"],
    "labels": ["string"]
  },
  "feature_areas": [
    {
      "epic": "KEY: Title",
      "description": "string",
      "stories": ["..."],
      "acceptance_criteria": ["..."],
      "risk_indicators": ["security", "third-party integration"]
    }
  ],
  "cross_cutting_concerns": ["string"],
  "technical_context": "string",
  "all_comments_summary": "string"
}
```

### Template Parser Output
```json
{
  "sections": [
    {
      "number": "1",
      "title": "Introduction",
      "subsections": [
        {"number": "1.1", "title": "Purpose", "subsections": []},
        {"number": "1.2", "title": "Scope", "subsections": []}
      ]
    }
  ],
  "raw_text": "full extracted text for fallback"
}
```

### Generation Request
```json
{
  "jira_ticket_ids": ["VMO-1", "VMO-2"],
  "fetch_children": true,
  "additional_context": "string",
  "provider": "groq | ollama",
  "model": "string",
  "depth": "standard | detailed | comprehensive",
  "focus_areas": ["functional", "performance", "security", "automation", "api"],
  "temperature": 0.3
}
```

### SSE Stream Events
```json
{"type": "status", "stage": 1, "message": "Analyzing JIRA context..."}
{"type": "status", "stage": 2, "message": "Parsing template structure..."}
{"type": "section_start", "section": "1. Introduction"}
{"type": "content", "text": "chunk of generated text..."}
{"type": "section_complete", "section": "1. Introduction"}
{"type": "done", "total_tokens_used": 15420, "generation_time_seconds": 45}
```

---

## Template Structure (from teststrategy.pdf — 19 pages, 13 sections)

1. Introduction (1.1 Purpose, 1.2 Scope, 1.3 Objectives, 1.4 References)
2. Project Overview (2.1 Description, 2.2 Stakeholders, 2.3 Architecture, 2.4 Key Business Flows)
3. Test Approach & Methodology (3.1 Philosophy, 3.2 Testing Levels [Unit/Integration/System/UAT], 3.3 Testing Types [Functional/Regression/Performance/Security/API/Accessibility/Compatibility/DR])
4. Test Automation Strategy (4.1 Approach, 4.2 Framework & Tools, 4.3 Coverage Targets, 4.4 CI/CD)
5. Test Environment Strategy (5.1 Topology, 5.2 Test Data Management, 5.3 Environment Management)
6. Defect Management Strategy (6.1 Lifecycle, 6.2 Severity & Priority Matrix, 6.3 SLA & Resolution Targets, 6.4 Tracking & Reporting)
7. Risk-Based Testing & Risk Management (7.1 Assessment Framework, 7.2 Risk Register, 7.3 Test Prioritization)
8. Entry & Exit Criteria (8.1 Entry, 8.2 Exit)
9. Test Metrics, KPIs & Reporting (9.1 Key Metrics, 9.2 Reporting Cadence, 9.3 Tools)
10. Roles and Responsibilities
11. Test Schedule & Milestones (11.1 Schedule, 11.2 Quality Gates)
12. Communication & Escalation Plan (12.1 Matrix, 12.2 Escalation Path)
13. Appendices (13.1 Glossary, 13.2 Assumptions, 13.3 Constraints, 13.4 Dependencies)

---

## Behavioral Rules

1. **Strategic, not tactical** — Generate test STRATEGY (why/what/how/who/when), never individual test cases
2. **Template fidelity** — Follow the PDF template structure exactly, fill EVERY section with substantive content
3. **Context-driven** — Derive specific recommendations from JIRA signals (e.g., "payment" tickets → security emphasis)
4. **Cross-reference consistency** — Tools mentioned in Section 4 must appear in Section 5 and Section 9
5. **Never expose API keys to frontend** — All LLM and JIRA calls go through backend only
6. **Sectional generation** — For Detailed/Comprehensive depth, generate section-by-section to avoid token limits
7. **ADF parsing is mandatory** — JIRA Cloud descriptions are Atlassian Document Format JSON, not plain text
8. **Context optimization** — When 10+ tickets exceed model limits, truncate by priority (keep titles/types always, trim comments first)
9. **Graceful degradation** — If PDF template parsing fails, fall back to regex section numbering patterns
10. **Single-command startup** — App must be launchable with one command (`start.sh` / `start.bat`)

---

## Architectural Invariants

- Follow B.L.A.S.T. protocol phases in order
- All tools in `tools/` must be deterministic and atomic
- All secrets stored in `.env`, never hardcoded
- All intermediate files go in `.tmp/`
- SQLite DB must auto-create on first run (use `create_all()` at startup)
- CORS configured for dev (frontend :5173, backend :8000)
- Update this file ONLY when: a schema changes, a rule is added, or architecture is modified

---

## Project Structure
```
teststrategy-agent/
├── backend/
│   ├── main.py                  # FastAPI entry point, CORS, static serving
│   ├── config.py                # Settings (.env read/write)
│   ├── database.py              # SQLAlchemy models & session (SQLite)
│   ├── models.py                # Pydantic request/response models
│   ├── routers/
│   │   ├── jira.py              # /api/jira/* endpoints
│   │   ├── generator.py         # /api/generate/* (SSE streaming)
│   │   ├── history.py           # /api/history/* CRUD
│   │   ├── settings.py          # /api/settings/*
│   │   ├── template.py          # /api/template/*
│   │   └── llm.py               # /api/llm/* (test, list models)
│   ├── services/
│   │   ├── jira_client.py       # JIRA REST API integration
│   │   ├── jira_aggregator.py   # Multi-ticket context aggregation
│   │   ├── template_parser.py   # PDF template extraction
│   │   ├── llm_provider.py      # Groq & Ollama abstraction
│   │   ├── prompt_builder.py    # LLM prompt construction (CORE)
│   │   ├── context_optimizer.py # Token budget management
│   │   └── export_service.py    # PDF and DOCX generation
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/               # Generator, History, Settings
│   │   ├── components/          # Header, JiraInput, StreamOutput, etc.
│   │   └── api/client.js        # Backend API wrappers
│   ├── package.json
│   └── vite.config.js
├── .env
├── teststrategy.pdf             # Default template
├── start.sh / start.bat
└── README.md
```

---

## Groq Model Registry (Updated from Research)

**NOTE:** The original spec listed `mixtral-8x7b-32768` and `gemma2-9b-it` — both are **DEPRECATED and removed** from Groq.

| Model ID | Context Window | Max Output | Use Case |
|---|---|---|---|
| `llama-3.3-70b-versatile` | 131K | 32K | Primary — best quality |
| `llama-3.1-8b-instant` | 131K | 131K | Fast — highest speed |
| `deepseek-r1-distill-llama-70b` | 131K | 16K | Reasoning — strategic analysis |
| `qwen-qwq-32b` | 131K | 16K | Alternative reasoning |
| `meta-llama/llama-4-scout-17b-16e-instruct` | 131K | 8K | Vision + multimodal |

---

## Maintenance Log

### 2026-02-16 — Phase 3 Complete (Architect)
- **Status:** Full-stack application implemented
- **Components:** 
  - 5 Architecture SOPs
  - 7 Backend services (jira_client, jira_aggregator, template_parser, llm_provider, prompt_builder, context_optimizer, export_service)
  - 6 API routers (jira, llm, template, settings, history, generator)
  - 3 React pages (Generator, History, Settings)
  - 2 Startup scripts (start.sh, start.bat)
- **Lines of Code:** ~8000+ (backend + frontend)
- **Known Limitations:** 
  - Frontend TOC sidebar not implemented (nice-to-have)
  - Section-by-section regeneration UI not implemented (API exists)
  - Compare feature in History page not implemented

### API Endpoints Summary
| Router | Endpoints |
|--------|-----------|
| /api/jira | GET /ticket/{id}, POST /tickets, GET /ticket/{id}/children, GET /test-connection, POST /aggregate |
| /api/llm | GET /providers, GET /models/{provider}, POST /test |
| /api/template | GET /preview, POST /upload, GET /current |
| /api/settings | GET /, PUT /, GET /defaults |
| /api/history | GET /, GET /{id}, DELETE /{id}, POST /{id}/clone |
| /api/generate | POST /stream (SSE), POST /section, POST /export/pdf, POST /export/docx |

### Environment Variables
```env
# Required
JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN
GROQ_API_KEY (or Ollama setup)

# Optional (have defaults)
JIRA_ACCEPTANCE_CRITERIA_FIELD=customfield_10016
GROQ_DEFAULT_MODEL=llama-3.3-70b-versatile
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3.1
DEFAULT_PROVIDER=groq
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=8192
TEMPLATE_PATH=./teststrategy.pdf
DEFAULT_DEPTH=detailed
```

### Next Steps for Production
1. Add authentication/authorization (currently none)
2. Add more comprehensive error logging
3. Implement integration tests
4. Add Docker support for easier deployment
5. Implement caching for JIRA data
6. Add support for JIRA Server (not just Cloud)
