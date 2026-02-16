# SOP: Context Optimization

## Purpose
Manage token budget to fit JIRA context within model limits while preserving critical information.

## Input
- Aggregated JIRA context
- Provider and model name
- Desired output token count

## Output
- Optimized context
- Metadata with utilization statistics

## Token Budget Calculation
```
context_window = model_specific (e.g., 131072 for llama-3.3-70b)
reserved = system_prompt + template_structure + output_tokens + buffer
available = context_window - reserved
```

## Optimization Levels (Progressive)

### Level 0: No Optimization
- All data included
- Use when: tokens < available

### Level 1: Trim Comments
- Remove `all_comments_summary`
- Comments in tickets already limited to last 5

### Level 2: Summarize Descriptions
- Truncate low/medium priority ticket descriptions to 200 chars
- Keep full descriptions for Critical/High priority

### Level 3: Trim Extras
- Limit acceptance criteria to 3 per epic
- Max 10 stories per epic (simplified: key, summary, type, priority)
- Limit cross-cutting concerns to 3 items

### Level 4: Essential Only
- Keep: ticket titles, types, priorities, epic structure
- Remove: descriptions, AC, comments, linked issues
- Last resort before failure

## Priority Preservation (ALWAYS KEEP)
1. All ticket keys and summaries
2. Issue types and priorities
3. Epic structure
4. Component and label lists

## Output Metadata
```json
{
  "context_window": 131072,
  "reserved": 11500,
  "available_for_context": 119572,
  "original_tokens": 150000,
  "final_tokens": 80000,
  "utilization_pct": 66.9,
  "optimization_level": 2,
  "truncated": true
}
```

## Sectional Generation Threshold
Use sectional generation when:
- required_output > (max_output * 0.8)
- For Comprehensive depth on most models
- When context optimization reaches level 3+
