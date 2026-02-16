# SOP: LLM Prompt Construction & Generation

## Purpose
Construct effective prompts and generate test strategy content using LLMs.

## Input
- Template section structure
- Aggregated JIRA context
- Generation parameters (depth, focus areas, temperature)

## Output
- Generated test strategy content in Markdown
- SSE streaming events for real-time UI updates

## Procedure

### 1. System Prompt
```
You are a Principal QA Architect and Test Strategist with 20+ years experience...
[Full system prompt in services/prompt_builder.py]
```

### 2. User Prompt Construction
Include:
- **Depth instruction** (standard/detailed/comprehensive word counts)
- **Template structure** (section hierarchy)
- **JIRA context** (project summary, feature areas, cross-cutting concerns)
- **Focus areas** (selected testing domains to emphasize)
- **Additional context** (user-provided project info)

### 3. Generation Modes

#### Single-Pass Mode
- Use when: Standard depth, <4000 tokens output
- Send one prompt, receive complete strategy

#### Sectional Mode
- Use when: Detailed/Comprehensive depth
- Generate section-by-section with context from previous sections
- Feed each completed section as context for next
- Benefits: Avoids token limits, enables per-section regeneration

### 4. Streaming Protocol (SSE)
Events:
- `status`: Stage updates (1-4)
- `section_start`: Beginning new section
- `content`: Text chunk
- `section_complete`: Section finished
- `done`: Generation complete with stats
- `error`: Error with code

### 5. Provider Abstraction
- **Groq**: Use `AsyncGroq` with streaming
- **Ollama**: Use HTTP `/api/chat` with streaming
- Both implement `LLMProvider` interface

## Depth Specifications
| Depth | Words/Section | Total Words | Output Tokens |
|-------|---------------|-------------|---------------|
| Standard | 200-400 | 3,000-5,000 | 4,000 |
| Detailed | 400-700 | 5,000-8,000 | 8,000 |
| Comprehensive | 600-1000 | 8,000-12,000 | 12,000 |

## Error Handling
- Rate limit: Exponential backoff with countdown
- Context length: Switch to sectional mode
- Auth failure: Prompt user to check settings
- Timeout (>5 min): Cancel and suggest simpler model
