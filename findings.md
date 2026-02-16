# Findings — TestStrategy Agent

## Source Documents
- **`TestStrategy_Agent_Prompt.md`** — 762-line detailed specification covering full-stack architecture, API endpoints, service logic, UI design, error handling, and prompt engineering
- **`teststrategy.pdf`** — 19-page enterprise test strategy template with 13 major sections and 40+ subsections

---

## Phase 1 Research: Technology Deep Dive

### 1. JIRA Cloud REST API v3

**Authentication:**
```python
# Basic Auth: base64(email:api_token)
import base64
auth = base64.b64encode(f"{email}:{api_token}".encode()).decode()
headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}
```

**Single Ticket Fetch:**
- Endpoint: `GET {JIRA_BASE_URL}/rest/api/3/issue/{ticket_id}`
- Key fields: `fields.summary`, `fields.description` (ADF JSON), `fields.issuetype.name`, `fields.status.name`, `fields.priority.name`, `fields.labels`, `fields.components`, `fields.comment.comments`, `fields.issuelinks`, `fields.subtasks`, `fields.customfield_10016` (acceptance criteria), `fields.fixVersions`

**ADF (Atlassian Document Format) Parsing — CRITICAL:**
JIRA Cloud descriptions are NOT plain text. They are nested JSON in ADF format:
```python
def adf_to_text(adf_node):
    """Convert Atlassian Document Format JSON to plain text."""
    if adf_node is None:
        return ""
    if isinstance(adf_node, str):
        return adf_node

    text_parts = []
    node_type = adf_node.get("type", "")

    if node_type == "text":
        return adf_node.get("text", "")
    elif node_type == "hardBreak":
        return "\n"
    elif node_type == "mention":
        return adf_node.get("attrs", {}).get("text", "")

    for child in adf_node.get("content", []):
        text_parts.append(adf_to_text(child))

    result = "".join(text_parts)

    # Add formatting based on node type
    if node_type in ("paragraph", "heading"):
        result += "\n"
    elif node_type == "bulletList":
        pass  # bullets handled by listItem
    elif node_type == "listItem":
        result = "• " + result
    elif node_type == "codeBlock":
        result = f"```\n{result}\n```\n"

    return result
```

**Multi-Ticket Fetch via JQL:**
- Endpoint: `GET {JIRA_BASE_URL}/rest/api/3/search`
- Params: `jql=key in (VMO-1, VMO-2, VMO-3)&maxResults=50&startAt=0`
- Pagination: Use `startAt` and `maxResults` (max 50 per page), check `total` in response
- Project-wide: `jql=project=VMO AND issuetype=Epic`

**Child Ticket Discovery:**
- Epics → Stories: `jql="Epic Link"={epic_key}` OR `jql=parent={epic_key}`
- Stories → Subtasks: Already in `fields.subtasks` array
- Linked Issues: In `fields.issuelinks` (inward/outward issue objects)
- Recursion: Fetch 1 level deep only to avoid API overload

**Rate Limiting:**
- JIRA Cloud uses adaptive rate limiting (no fixed published numbers)
- Practical guideline: stay under ~100 requests per minute per user
- On 429: read `Retry-After` header for wait duration
- Some instances return 403 instead of 429 for rate limits — check response body
- Use `httpx.AsyncClient` with retry logic and exponential backoff

**JIRA API Best Practices:**
- Use `fields` param to request only needed fields (reduces server load)
- Batch requests via JQL search (`key in (A-1, A-2)`) instead of one-by-one fetches
- Use POST for `/rest/api/3/search` (avoids URL encoding issues with complex JQL)
- Max pagination: 100 results per request (even if maxResults set higher)
- `customfield_10016` for acceptance criteria is NOT universal — varies per instance. Provide configurable field mapping in Settings.
- Child discovery: try `"Epic Link"` JQL first (classic projects), fall back to `parent=` (next-gen projects)

---

### 2. Groq SDK

**Installation:** `pip install groq`

**Available Models (Current):**

| Model ID | Context Window | Max Output Tokens | Speed |
|---|---|---|---|
| `llama-3.3-70b-versatile` | 131,072 | 32,768 | 280 t/s |
| `llama-3.1-8b-instant` | 131,072 | 131,072 | 560 t/s |
| `deepseek-r1-distill-llama-70b` | 131,072 | 16,384 | ~200 t/s |
| `qwen-qwq-32b` | 131,072 | 16,384 | ~300 t/s |
| `meta-llama/llama-4-scout-17b-16e-instruct` | 131,072 | 8,192 | ~400 t/s |

**IMPORTANT:** `mixtral-8x7b-32768` and `gemma-7b-it` are **DEPRECATED and removed** from Groq. Must update the spec's model list.

**Streaming Example:**
```python
from groq import AsyncGroq

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

async def generate_stream(prompt, system_prompt, model, temperature, max_tokens):
    stream = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
```

**Rate Limits (Free Tier):**
- Requests per minute (RPM): ~30
- Tokens per minute (TPM): ~6,000-14,400 depending on model
- Tokens per day (TPD): ~500,000
- Rate limit headers: `x-ratelimit-limit-requests`, `x-ratelimit-remaining-requests`, `x-ratelimit-reset-requests`
- On 429: Read `retry-after` header, show countdown timer in UI

**Error Handling:**
- 401: Invalid API key → "Update Groq API key in Settings"
- 429: Rate limited → exponential backoff with countdown
- 413: Context too large → switch to sectional generation
- Connection errors → "Check internet connection"

**Streaming Details:**
- `chunk.choices[0].finish_reason`: `None` while streaming, `"stop"` on normal end, `"length"` when hitting max_tokens (truncated — important for detecting sectional generation overflow)
- Usage stats on final chunk: `chunk.x_groq.usage` has `prompt_tokens`, `completion_tokens`, `total_tokens`
- Must use `AsyncGroq` (not `Groq`) for non-blocking FastAPI endpoints

**Token Estimation:**
- No official `groq.count_tokens()` — use `tiktoken` with `cl100k_base` encoding + 10% safety margin
- Or rough fallback: ~4 characters per token for English text
- List models programmatically: `client.models.list()` returns model IDs + context windows

**Groq SDK Exception Classes:**
```python
from groq import (
    AuthenticationError,   # 401
    RateLimitError,        # 429
    BadRequestError,       # 400 (includes context_length_exceeded)
    APIConnectionError,    # Network failure
    APIStatusError,        # 500/502/503
)
```

**Key Insight for Sectional Generation:**
With 32K max output tokens on `llama-3.3-70b-versatile` and 131K context window, we CAN generate "Standard" depth (~5K words ≈ ~7K tokens) in a single call. But "Comprehensive" depth (~12K words ≈ ~16K tokens) should still use sectional generation for quality.

**Context Overflow Fallback Strategy:**
If `BadRequestError` contains "context_length_exceeded", progressively trim JIRA context:
Level 1: Remove comments → Level 2: Summarize low-priority descriptions → Level 3: Remove linked issues → Level 4: Keep only titles/types/priorities

---

### 3. Ollama API

**List Models:**
```python
import httpx

async def list_models(base_url="http://localhost:11434"):
    response = await httpx.AsyncClient().get(f"{base_url}/api/tags")
    data = response.json()
    return [model["name"] for model in data.get("models", [])]
```

**Streaming Chat:**
```python
import ollama

# Using ollama Python package
async def ollama_stream(prompt, system_prompt, model, temperature):
    client = ollama.AsyncClient()
    stream = await client.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        stream=True,
        options={"temperature": temperature}
    )
    async for chunk in stream:
        if chunk["message"]["content"]:
            yield chunk["message"]["content"]
```

**Raw HTTP Alternative (no package dependency):**
```python
async def ollama_stream_http(prompt, system_prompt, model, base_url="http://localhost:11434"):
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", f"{base_url}/api/chat", json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": True
        }) as response:
            async for line in response.aiter_lines():
                data = json.loads(line)
                if data.get("message", {}).get("content"):
                    yield data["message"]["content"]
```

**Connection Testing:**
```python
async def test_ollama(base_url="http://localhost:11434"):
    try:
        response = await httpx.AsyncClient().get(f"{base_url}/api/tags", timeout=5)
        return response.status_code == 200
    except httpx.ConnectError:
        return False  # "Ollama not running. Start with: ollama serve"
```

**Error Handling:**
- `ConnectionRefusedError` → "Cannot connect to Ollama. Start with: `ollama serve`"
- Model not found → "Model not available. Pull it first: `ollama pull {name}`"
- Out of memory → "Try a smaller model or reduce context"

**CRITICAL: Default Context is Only 4,096 Tokens!**
Ollama defaults to 4,096 token context for ALL models regardless of max capability. Must explicitly set `num_ctx` in request options:
```python
options={"temperature": temperature, "num_ctx": 32768}  # or 16384 for smaller models
```

**Common Model Context Windows:**
| Model | Default Context | Max Context | Notes |
|---|---|---|---|
| llama3.1 (8B) | 4,096 | 128K | Must set num_ctx explicitly |
| llama3.1 (70B) | 4,096 | 128K | Needs significant RAM/VRAM |
| mistral (7B) | 4,096 | 32K | Good quality-to-size ratio |
| qwen2.5 (7B) | 4,096 | 128K | Multilingual, strong reasoning |
| gemma2 (9B) | 4,096 | 8K | Limited context window |

---

### 4. pdfplumber — Template Parsing

**Installation:** `pip install pdfplumber`

**Recommended Approach: Hybrid (regex + font analysis)**

```python
import pdfplumber
import re

def parse_template(pdf_path):
    sections = []
    full_text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

    # Regex-based section detection (most reliable for numbered sections)
    section_pattern = re.compile(
        r'^(\d+(?:\.\d+)*)\s+(.+)$', re.MULTILINE
    )

    for match in section_pattern.finditer(full_text):
        number = match.group(1)
        title = match.group(2).strip()
        depth = number.count('.') + 1
        sections.append({
            "number": number,
            "title": title,
            "depth": depth,
            "subsections": []
        })

    # Build hierarchy from flat list
    return build_hierarchy(sections)

def build_hierarchy(flat_sections):
    root = []
    stack = []

    for section in flat_sections:
        while stack and stack[-1]["depth"] >= section["depth"]:
            stack.pop()

        if stack:
            stack[-1]["subsections"].append(section)
        else:
            root.append(section)

        stack.append(section)

    return root
```

**Font-based fallback (for non-numbered PDFs):**
```python
def extract_headings_by_font(pdf_path):
    headings = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for char in page.chars:
                # Detect larger/bold fonts as headings
                if char["size"] > 14 or "Bold" in char.get("fontname", ""):
                    headings.append(char)
    return headings
```

**Recommended: Hybrid Approach (Font-First, Regex Fallback)**
1. Extract character-level data via `page.chars` — each char has `fontname`, `size`, `top`, `x0`
2. Detect bold fonts by checking `"bold" in fontname.lower()` (e.g., `"BCDEEE+Calibri-Bold"`)
3. Determine body text size (most common `size` value), headings are larger/bolder
4. Cross-validate with regex: lines matching `r'^(\d{1,2}(?:\.\d{1,2}){0,3})\s+([A-Z].+)$'` AND having larger/bold fonts = confirmed sections
5. If font analysis yields <10 sections, fall back to pure regex
6. Use `page.extract_text(layout=True)` for multi-column documents

**Key Decision:** For our `teststrategy.pdf` template, the hybrid approach is best — font analysis validates regex matches, reducing false positives from numbered lists in body text.

---

### 5. FastAPI SSE (Server-Sent Events)

**Installation:** `pip install sse-starlette`

**Streaming Endpoint Pattern:**
```python
from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse
import json

app = FastAPI()

@app.post("/api/generate/stream")
async def generate_stream(request: Request, body: GenerateRequest):
    async def event_generator():
        # Stage 1: Analyzing context
        yield json.dumps({"type": "status", "stage": 1, "message": "Analyzing JIRA context..."})

        # Stage 2: Parsing template
        yield json.dumps({"type": "status", "stage": 2, "message": "Parsing template structure..."})

        # Stage 3: Generate section by section
        for section in template_sections:
            yield json.dumps({"type": "section_start", "section": section["title"]})

            async for chunk in llm_provider.generate_stream(prompt):
                if await request.is_disconnected():
                    return
                yield json.dumps({"type": "content", "text": chunk})

            yield json.dumps({"type": "section_complete", "section": section["title"]})

        # Done
        yield json.dumps({"type": "done", "total_tokens_used": token_count})

    return EventSourceResponse(event_generator())
```

**React Frontend Consumption:**
```javascript
const eventSource = new EventSource('/api/generate/stream', {
    method: 'POST',  // Use fetch with ReadableStream for POST
});

// Better approach for POST requests:
async function streamGenerate(requestBody) {
    const response = await fetch('/api/generate/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        const lines = text.split('\n').filter(line => line.startsWith('data: '));

        for (const line of lines) {
            const data = JSON.parse(line.slice(6));  // Remove "data: " prefix
            handleEvent(data);
        }
    }
}
```

**EventSourceResponse Configuration:**
```python
EventSourceResponse(
    content=event_generator(request),
    ping=30,  # Keepalive every 30s — prevents proxy/load balancer timeouts
)
```

**Critical Implementation Details:**
- Parse POST body (`await request.json()`) BEFORE entering the generator function
- Check `await request.is_disconnected()` in the generation loop to stop on client disconnect
- Use `asyncio.timeout(300)` (5 min) per section to prevent hung generations
- Add `error` event type for mid-stream error reporting (JIRA failures, rate limits)
- Named events via `ServerSentEvent(data=..., event="content")` are optional but help with frontend `addEventListener`

**Key Decision:** Use `sse-starlette` with `EventSourceResponse` for backend. On frontend, use `fetch` with `ReadableStream` (not `EventSource`) because SSE POST requests aren't natively supported by `EventSource` API.

---

## Key Architectural Discoveries

### Template Structure (from PDF analysis)
The template has a well-defined hierarchy with numbered sections (1-13), each with subsections (e.g., 3.2.1 Unit Testing). Regex-based parsing is the primary approach; font analysis is fallback.

### Critical Technical Challenges
1. **ADF Parsing** — JIRA Cloud descriptions use Atlassian Document Format (nested JSON). Solution: recursive `adf_to_text()` converter.
2. **Sectional Generation** — Test strategies can be 5,000-12,000 words. Solution: section-by-section generation with previous sections as context.
3. **Context Window Management** — 10+ JIRA tickets can exceed limits. Solution: intelligent truncation by priority.
4. **Groq Model Updates** — `mixtral-8x7b-32768` and `gemma-7b-it` are DEPRECATED. Must use `llama-3.3-70b-versatile` (32K output) and `llama-3.1-8b-instant` (131K output) instead.

### Updated Model Recommendations
- **Primary (Groq):** `llama-3.3-70b-versatile` — 131K context, 32K output, best quality
- **Fast (Groq):** `llama-3.1-8b-instant` — 131K context, 131K output, fastest
- **Reasoning (Groq):** `deepseek-r1-distill-llama-70b` — good for strategic analysis
- **Local (Ollama):** `llama3.1` (8B/70B) — 128K context, no API costs

### API Endpoints Required (20 total)
- JIRA: 4 endpoints (fetch single, fetch multi, fetch children, test connection)
- Generator: 4 endpoints (stream generate, regenerate section, export PDF, export DOCX)
- LLM: 3 endpoints (list providers, list models, test connection)
- History: 4 endpoints (list, get, delete, clone)
- Settings: 2 endpoints (get, update)
- Template: 2 endpoints (preview, upload)

### UI Pages: 3
1. **Generator** — Main workspace with 6 vertical sections
2. **History** — Strategy list with search/filter/compare
3. **Settings** — JIRA, Groq, Ollama, Template, Generation Defaults, Export config

## Constraints
- Must run entirely on user's local machine
- Single-command startup required
- Python 3.10+ and Node.js 18+ prerequisites
- SQLite only (no external database)
- Groq free tier rate limits may slow "Comprehensive" generation

## Python Dependencies (backend/requirements.txt)
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
python-dotenv>=1.0.0
httpx>=0.25.0
pdfplumber>=0.10.0
reportlab>=4.0.0
python-docx>=1.0.0
groq>=0.4.0
ollama>=0.1.0
sse-starlette>=1.8.0
pydantic>=2.5.0
python-multipart>=0.0.6
```
