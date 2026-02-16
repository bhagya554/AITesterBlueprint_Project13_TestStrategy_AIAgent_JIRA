# SOP: JIRA Data Fetching

## Purpose
Fetch ticket data from JIRA Cloud REST API v3 for aggregation and strategy generation.

## Input
- `ticket_ids`: List of JIRA ticket keys (e.g., ["VMO-1", "VMO-2"])
- `fetch_children`: Boolean to fetch linked issues and subtasks

## Output
- List of parsed ticket dictionaries with extracted fields
- List of error messages for failed fetches

## Procedure

### 1. Authentication
- Use Basic Auth with base64-encoded `email:api_token`
- Headers: `Authorization: Basic {encoded}`, `Accept: application/json`

### 2. Single Ticket Fetch
- Endpoint: `GET {JIRA_BASE_URL}/rest/api/3/issue/{ticket_id}`
- Fields: summary, description (ADF), issuetype, status, priority, labels, components, comments, issuelinks, subtasks, fixVersions, customfield_10016 (AC)

### 3. Multi-Ticket Fetch
- Use JQL search: `GET /rest/api/3/search?jql=key in (VMO-1, VMO-2)&maxResults=50`
- Paginate with `startAt` parameter
- Batch requests preferred over individual fetches

### 4. ADF Parsing (CRITICAL)
- JIRA Cloud descriptions are Atlassian Document Format (nested JSON)
- Use recursive `adf_to_text()` converter
- Handle: text, hardBreak, mention, paragraph, heading, bulletList, listItem, codeBlock

### 5. Child Discovery
- For Epics: Use JQL `"Epic Link"={key}` OR `parent={key}`
- For Stories: Subtasks already in `fields.subtasks`
- Recursion depth: 1 level max to avoid API overload

## Error Handling
| Error | Response |
|-------|----------|
| 401 Unauthorized | "Check JIRA email and API token" |
| 404 Not Found | "Ticket not found or no access" |
| 429 Rate Limit | Wait and retry with exponential backoff |
| Connection Error | "Check JIRA_BASE_URL and internet" |

## Edge Cases
1. **Missing custom fields**: AC field varies per instance (default: customfield_10016)
2. **Empty descriptions**: Return empty string, not null
3. **Epic without children**: Return empty list, not error
4. **Mixed project keys**: JQL handles this automatically
