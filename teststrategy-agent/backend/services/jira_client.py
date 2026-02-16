"""
JIRA REST API Client
Handles single/multi ticket fetching, ADF parsing, and child discovery
"""

import base64
import json
from typing import List, Dict, Optional, Any
import httpx
from config import get_settings


def get_jira_auth_headers() -> Dict[str, str]:
    """Build JIRA authentication headers."""
    settings = get_settings()
    auth_string = base64.b64encode(
        f"{settings.jira_email}:{settings.jira_api_token}".encode()
    ).decode()
    return {
        "Authorization": f"Basic {auth_string}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


def adf_to_text(adf_node: Any) -> str:
    """
    Convert Atlassian Document Format (ADF) JSON to plain text.
    JIRA Cloud descriptions are nested JSON, not plain text.
    """
    if adf_node is None:
        return ""
    if isinstance(adf_node, str):
        return adf_node
    
    text_parts = []
    node_type = adf_node.get("type", "") if isinstance(adf_node, dict) else ""
    
    if node_type == "text":
        text = adf_node.get("text", "")
        # Handle marks (formatting)
        marks = adf_node.get("marks", [])
        for mark in marks:
            mark_type = mark.get("type", "")
            if mark_type == "strong":
                text = f"**{text}**"
            elif mark_type == "em":
                text = f"*{text}*"
            elif mark_type == "code":
                text = f"`{text}`"
        return text
    
    elif node_type == "hardBreak":
        return "\n"
    
    elif node_type == "mention":
        return adf_node.get("attrs", {}).get("text", "")
    
    elif node_type == "emoji":
        return adf_node.get("attrs", {}).get("shortName", "")
    
    elif node_type == "inlineCard" or node_type == "blockCard":
        attrs = adf_node.get("attrs", {})
        url = attrs.get("url", "")
        return f" [{url}] " if url else ""
    
    # Process children recursively
    if isinstance(adf_node, dict):
        for child in adf_node.get("content", []):
            text_parts.append(adf_to_text(child))
    
    result = "".join(text_parts)
    
    # Add formatting based on node type
    if node_type == "paragraph":
        result += "\n"
    elif node_type == "heading":
        level = adf_node.get("attrs", {}).get("level", 1)
        result = f"{'#' * level} {result}\n"
    elif node_type == "bulletList":
        pass  # Handled by listItem
    elif node_type == "orderedList":
        pass  # Handled by listItem
    elif node_type == "listItem":
        result = f"• {result}\n"
    elif node_type == "codeBlock":
        language = adf_node.get("attrs", {}).get("language", "")
        result = f"```{language}\n{result}\n```\n"
    elif node_type == "blockquote":
        result = f"> {result}\n"
    elif node_type == "panel":
        panel_type = adf_node.get("attrs", {}).get("panelType", "info")
        result = f"[{panel_type.upper()}] {result}\n"
    elif node_type == "table":
        result += "\n"
    elif node_type == "tableRow":
        result = f"| {result}\n"
    elif node_type == "tableCell" or node_type == "tableHeader":
        result = f"{result} | "
    
    return result


def parse_jira_ticket(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse JIRA API response into clean ticket dict."""
    settings = get_settings()
    fields = data.get("fields", {})
    
    # Get description (handle ADF format)
    description_raw = fields.get("description")
    description = adf_to_text(description_raw) if description_raw else None
    
    # Get acceptance criteria from custom field
    ac_field = settings.jira_acceptance_criteria_field or "customfield_10016"
    acceptance_criteria_raw = fields.get(ac_field)
    acceptance_criteria = None
    if acceptance_criteria_raw:
        if isinstance(acceptance_criteria_raw, dict):
            acceptance_criteria = adf_to_text(acceptance_criteria_raw)
        else:
            acceptance_criteria = str(acceptance_criteria_raw)
    
    # Parse comments
    comments = []
    comment_data = fields.get("comment", {}).get("comments", [])
    for comment in comment_data[-5:]:  # Last 5 comments
        author = comment.get("author", {}).get("displayName", "Unknown")
        body = adf_to_text(comment.get("body")) if comment.get("body") else ""
        created = comment.get("created", "")
        comments.append({
            "author": author,
            "body": body[:500] if body else "",  # Truncate long comments
            "date": created[:10] if created else ""
        })
    
    # Parse linked issues
    linked_issues = []
    for link in fields.get("issuelinks", []):
        link_type = link.get("type", {}).get("name", "")
        if "inwardIssue" in link:
            issue = link["inwardIssue"]
            linked_issues.append({
                "type": f"{link_type} (inward)",
                "key": issue.get("key", ""),
                "summary": issue.get("fields", {}).get("summary", "")
            })
        if "outwardIssue" in link:
            issue = link["outwardIssue"]
            linked_issues.append({
                "type": f"{link_type} (outward)",
                "key": issue.get("key", ""),
                "summary": issue.get("fields", {}).get("summary", "")
            })
    
    # Parse subtasks
    subtasks = []
    for subtask in fields.get("subtasks", []):
        subtasks.append({
            "key": subtask.get("key", ""),
            "summary": subtask.get("fields", {}).get("summary", ""),
            "status": subtask.get("fields", {}).get("status", {}).get("name", "")
        })
    
    # Parse components
    components = [c.get("name", "") for c in fields.get("components", [])]
    
    # Parse fix versions
    fix_versions = [v.get("name", "") for v in fields.get("fixVersions", [])]
    
    # Parse sprint info (customfield_10020 is common for sprint)
    sprint = None
    sprints = fields.get("customfield_10020", [])
    if sprints and isinstance(sprints, list):
        sprint_data = sprints[0]
        if isinstance(sprint_data, dict):
            sprint = sprint_data.get("name", "")
        elif isinstance(sprint_data, str):
            sprint = sprint_data
    
    return {
        "key": data.get("key", ""),
        "summary": fields.get("summary", ""),
        "description": description,
        "issue_type": fields.get("issuetype", {}).get("name", ""),
        "status": fields.get("status", {}).get("name", ""),
        "priority": fields.get("priority", {}).get("name", ""),
        "labels": fields.get("labels", []),
        "components": components,
        "acceptance_criteria": acceptance_criteria,
        "comments": comments,
        "linked_issues": linked_issues,
        "subtasks": subtasks,
        "fix_versions": fix_versions,
        "sprint": sprint,
        "url": f"{settings.jira_base_url}/browse/{data.get('key', '')}"
    }


async def fetch_ticket(ticket_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single JIRA ticket by ID."""
    settings = get_settings()
    base_url = settings.jira_base_url.rstrip('/')
    
    url = f"{base_url}/rest/api/3/issue/{ticket_id}"
    headers = get_jira_auth_headers()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            
            if response.status_code == 200:
                return parse_jira_ticket(response.json())
            elif response.status_code == 404:
                return None
            else:
                raise Exception(f"JIRA API error: {response.status_code} - {response.text[:200]}")
                
        except httpx.TimeoutException:
            raise Exception("JIRA request timed out")
        except httpx.ConnectError:
            raise Exception("Cannot connect to JIRA server")


async def fetch_tickets(ticket_ids: List[str]) -> tuple[List[Dict], List[str]]:
    """
    Fetch multiple JIRA tickets.
    Falls back to individual fetches if JQL search fails.
    Returns (successful_tickets, error_messages).
    """
    if not ticket_ids:
        return [], []
    
    all_issues = []
    errors = []
    
    # Try individual ticket fetching (more reliable than JQL for some JIRA instances)
    for ticket_id in ticket_ids:
        try:
            ticket = await fetch_ticket(ticket_id)
            if ticket:
                all_issues.append(ticket)
            else:
                errors.append(f"Ticket {ticket_id} not found")
        except Exception as e:
            errors.append(f"Error fetching {ticket_id}: {str(e)}")
    
    return all_issues, errors


async def fetch_children(epic_key: str) -> List[Dict[str, Any]]:
    """
    Fetch all child issues of an epic.
    Tries "Epic Link" field first (classic), then parent field (next-gen).
    """
    settings = get_settings()
    base_url = settings.jira_base_url.rstrip('/')
    headers = get_jira_auth_headers()
    
    # Try classic JQL first
    jql_queries = [
        f'"Epic Link" = {epic_key}',
        f'parent = {epic_key}',
    ]
    
    all_children = []
    
    async with httpx.AsyncClient() as client:
        for jql in jql_queries:
            url = f"{base_url}/rest/api/3/search"
            params = {
                "jql": jql,
                "maxResults": 100,
                "fields": "summary,description,issuetype,status,priority,labels,components,comment,issuelinks,subtasks,fixVersions,customfield_10016"
            }
            
            try:
                response = await client.get(url, headers=headers, params=params, timeout=30.0)
                
                if response.status_code == 200:
                    data = response.json()
                    issues = data.get("issues", [])
                    
                    for issue in issues:
                        all_children.append(parse_jira_ticket(issue))
                    
                    # If we got results, break (found the right query)
                    if issues:
                        break
                        
            except Exception:
                continue
    
    return all_children


async def test_connection() -> Dict[str, Any]:
    """Test JIRA connection and return user info."""
    settings = get_settings()
    base_url = settings.jira_base_url.rstrip('/')
    
    url = f"{base_url}/rest/api/3/myself"
    headers = get_jira_auth_headers()
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=10.0)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "display_name": data.get("displayName"),
                "email": data.get("emailAddress"),
                "account_id": data.get("accountId"),
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "message": response.text[:200]
            }
