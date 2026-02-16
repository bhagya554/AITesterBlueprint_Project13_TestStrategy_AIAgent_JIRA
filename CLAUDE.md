# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**TestStrategy Agent** — a production-grade, locally-hosted full-stack web app that auto-generates enterprise-level test strategy documents by pulling context from JIRA tickets and populating a PDF template using LLM (Groq/Ollama).

**Key distinction:** A Test Strategy is a strategic, project-wide document (why/what/how/who/when of testing) — NOT a test plan with individual test cases.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+ / FastAPI |
| Frontend | React 18 (Vite) / Tailwind CSS |
| Database | SQLite via SQLAlchemy |
| PDF Parse | pdfplumber |
| PDF/DOCX Export | ReportLab or WeasyPrint / python-docx |
| LLM | Groq SDK + Ollama |
| Config | `.env` via python-dotenv |

## B.L.A.S.T. Protocol

All work follows the phased protocol in `B.L.A.S.T.md`. **No code until discovery is complete and `gemini.md` has approved schemas.**

## Key Files

- `gemini.md` — **Project constitution (law)**: schemas, behavioral rules, architectural invariants
- `TestStrategy_Agent_Prompt.md` — Full 762-line specification (source of truth for requirements)
- `teststrategy.pdf` — 19-page test strategy template (13 sections, 40+ subsections)
- `task_plan.md` / `findings.md` / `progress.md` — Project memory (update after every task)

## Architecture

```
teststrategy-agent/
├── backend/
│   ├── main.py              # FastAPI entry, CORS, static serving
│   ├── config.py            # .env read/write
│   ├── database.py          # SQLAlchemy + SQLite
│   ├── models.py            # Pydantic models
│   ├── routers/             # 6 API routers (jira, generator, history, settings, template, llm)
│   └── services/            # 7 services (jira_client, jira_aggregator, template_parser,
│                            #   llm_provider, prompt_builder, context_optimizer, export_service)
├── frontend/src/
│   ├── pages/               # Generator, History, Settings
│   ├── components/          # Header, JiraInput, StreamOutput, DocumentView, etc.
│   └── api/client.js
├── .env
└── teststrategy.pdf
```

## Commands

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd frontend && npm install && npm run dev

# Production (single command)
./start.sh   # or start.bat on Windows
```

## Critical Implementation Rules

1. Never expose API keys to frontend — all LLM/JIRA calls go through backend
2. JIRA descriptions use ADF (Atlassian Document Format) JSON — must convert to plain text
3. Use sectional generation for Detailed/Comprehensive depth (section-by-section to avoid token limits)
4. Context optimizer must truncate intelligently when 10+ JIRA tickets exceed model limits
5. SQLite DB auto-creates on first run (`create_all()`)
6. SSE (Server-Sent Events) for real-time streaming output
7. If PDF template parsing fails, fall back to regex section numbering
