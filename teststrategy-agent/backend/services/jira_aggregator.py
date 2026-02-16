"""
JIRA Context Aggregator
Aggregates data from multiple JIRA tickets into structured context for LLM
"""

import re
from typing import List, Dict, Any, Optional
from collections import Counter


def extract_technical_signals(description: str) -> List[str]:
    """Extract technical signals from description text."""
    if not description:
        return []
    
    signals = []
    text_lower = description.lower()
    
    # Tech stack indicators
    tech_patterns = {
        "react": "React frontend",
        "angular": "Angular frontend", 
        "vue": "Vue.js frontend",
        "node.js": "Node.js backend",
        "python": "Python backend",
        "java": "Java backend",
        "spring": "Spring framework",
        "django": "Django framework",
        "flask": "Flask framework",
        "fastapi": "FastAPI framework",
        "postgresql": "PostgreSQL database",
        "mysql": "MySQL database",
        "mongodb": "MongoDB database",
        "redis": "Redis cache",
        "docker": "Docker containers",
        "kubernetes": "Kubernetes orchestration",
        "aws": "AWS cloud",
        "azure": "Azure cloud",
        "gcp": "Google Cloud Platform",
        "rest api": "REST API",
        "graphql": "GraphQL API",
        "grpc": "gRPC API",
        "microservice": "Microservices architecture",
        "serverless": "Serverless architecture",
        "lambda": "AWS Lambda",
    }
    
    for pattern, label in tech_patterns.items():
        if pattern in text_lower:
            signals.append(label)
    
    return list(set(signals))


def extract_risk_indicators(ticket: Dict[str, Any]) -> List[str]:
    """Extract risk indicators from a ticket."""
    indicators = []
    
    # Check labels
    risk_labels = ["security", "performance", "compliance", "critical", "production", "payment", "pii", "gdpr", "hipaa"]
    for label in ticket.get("labels", []):
        label_lower = label.lower()
        if any(risk in label_lower for risk in risk_labels):
            indicators.append(f"Label: {label}")
    
    # Check description for keywords
    description = ticket.get("description", "") or ""
    desc_lower = description.lower()
    
    risk_keywords = {
        "payment": "Payment processing involved",
        "credit card": "PCI DSS considerations",
        "pii": "Personal identifiable information",
        "gdpr": "GDPR compliance required",
        "hipaa": "HIPAA compliance required",
        "security": "Security considerations",
        "authentication": "Authentication system",
        "authorization": "Authorization system",
        "third-party": "Third-party integration",
        "external api": "External API dependency",
        "performance": "Performance requirements",
        "scale": "Scalability considerations",
        "concurrent": "Concurrency handling",
        "transaction": "Transaction handling",
        "migration": "Data migration involved",
        "legacy": "Legacy system integration",
    }
    
    for keyword, indicator in risk_keywords.items():
        if keyword in desc_lower:
            indicators.append(indicator)
    
    # Check priority
    priority = ticket.get("priority", "")
    if priority in ["Critical", "Highest"]:
        indicators.append(f"Critical priority")
    elif priority == "High":
        indicators.append(f"High priority")
    
    return list(set(indicators))


def aggregate_tickets(tickets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate multiple JIRA tickets into structured context.
    This is the main function that prepares context for the LLM.
    """
    if not tickets:
        return {
            "project_summary": {
                "total_tickets": 0,
                "epics": [],
                "issue_type_breakdown": {},
                "priority_breakdown": {},
                "components": [],
                "labels": [],
            },
            "feature_areas": [],
            "cross_cutting_concerns": [],
            "technical_context": None,
            "all_comments_summary": None,
        }
    
    # === Project Summary ===
    issue_types = Counter(t.get("issue_type", "Unknown") for t in tickets)
    priorities = Counter(t.get("priority") or "None" for t in tickets)
    
    all_components = set()
    all_labels = set()
    epics = []
    
    for ticket in tickets:
        all_components.update(ticket.get("components", []))
        all_labels.update(ticket.get("labels", []))
        
        if ticket.get("issue_type") == "Epic":
            epics.append(f"{ticket['key']}: {ticket['summary']}")
    
    project_summary = {
        "total_tickets": len(tickets),
        "epics": epics,
        "issue_type_breakdown": dict(issue_types),
        "priority_breakdown": dict(priorities),
        "components": sorted(all_components),
        "labels": sorted(all_labels),
    }
    
    # === Feature Areas ===
    # Group by Epic
    epic_tickets = {}
    orphan_tickets = []
    
    for ticket in tickets:
        if ticket.get("issue_type") == "Epic":
            if ticket["key"] not in epic_tickets:
                epic_tickets[ticket["key"]] = {
                    "epic": ticket,
                    "stories": []
                }
            else:
                epic_tickets[ticket["key"]]["epic"] = ticket
        else:
            # Try to find parent epic (would need additional lookup in real implementation)
            orphan_tickets.append(ticket)
    
    # Add orphan tickets to first epic or create pseudo-epic
    if orphan_tickets:
        if epic_tickets:
            # Add to first epic
            first_epic = list(epic_tickets.keys())[0]
            epic_tickets[first_epic]["stories"].extend(orphan_tickets)
        else:
            # Create pseudo-epic
            epic_tickets["GENERAL"] = {
                "epic": {
                    "key": "GENERAL",
                    "summary": "General Features",
                    "description": "Features not associated with a specific epic",
                },
                "stories": orphan_tickets
            }
    
    feature_areas = []
    all_risks = []
    all_technical_signals = []
    
    for epic_key, data in epic_tickets.items():
        epic = data["epic"]
        stories = data["stories"]
        
        # Collect acceptance criteria
        all_ac = []
        for story in stories:
            ac = story.get("acceptance_criteria")
            if ac:
                all_ac.append(f"[{story['key']}] {ac[:200]}...")
        
        # Collect risk indicators
        epic_risks = extract_risk_indicators(epic)
        all_risks.extend(epic_risks)
        
        for story in stories:
            story_risks = extract_risk_indicators(story)
            all_risks.extend(story_risks)
        
        # Extract technical signals
        tech_signals = extract_technical_signals(epic.get("description", ""))
        all_technical_signals.extend(tech_signals)
        
        for story in stories:
            signals = extract_technical_signals(story.get("description", ""))
            all_technical_signals.extend(signals)
        
        feature_areas.append({
            "epic_key": epic_key,
            "epic_title": epic.get("summary", ""),
            "description": epic.get("description", "")[:500] if epic.get("description") else None,
            "priority": epic.get("priority"),
            "stories": [
                {
                    "key": s["key"],
                    "summary": s["summary"],
                    "type": s.get("issue_type"),
                    "priority": s.get("priority"),
                }
                for s in stories
            ],
            "acceptance_criteria": all_ac[:10],  # Limit to 10
            "risk_indicators": list(set(epic_risks)),
        })
    
    # === Cross-Cutting Concerns ===
    concerns = []
    
    # Analyze labels for patterns
    label_counts = Counter()
    for ticket in tickets:
        label_counts.update(ticket.get("labels", []))
    
    common_labels = [label for label, count in label_counts.most_common(5) if count > 1]
    if common_labels:
        concerns.append(f"Common labels across tickets: {', '.join(common_labels)}")
    
    # Security mentions
    security_count = sum(1 for r in all_risks if "security" in r.lower() or "pci" in r.lower() or "gdpr" in r.lower())
    if security_count > 0:
        concerns.append(f"Security/compliance requirements noted in {security_count} tickets")
    
    # Performance mentions
    perf_count = sum(1 for r in all_risks if "performance" in r.lower() or "scale" in r.lower())
    if perf_count > 0:
        concerns.append(f"Performance/scalability concerns in {perf_count} tickets")
    
    # Integration points
    integration_count = sum(1 for r in all_risks if "integration" in r.lower() or "third-party" in r.lower() or "external" in r.lower())
    if integration_count > 0:
        concerns.append(f"External integrations mentioned in {integration_count} tickets")
    
    # Priority distribution
    critical_high = priorities.get("Critical", 0) + priorities.get("High", 0) + priorities.get("Highest", 0)
    if critical_high > 0:
        concerns.append(f"{critical_high} tickets marked as Critical/High priority")
    
    # === Technical Context ===
    unique_tech = list(set(all_technical_signals))
    technical_context = None
    if unique_tech:
        technical_context = f"Detected technology signals: {', '.join(unique_tech[:10])}"
    
    # === Comments Summary ===
    all_comments = []
    for ticket in tickets:
        for comment in ticket.get("comments", []):
            all_comments.append(f"[{ticket['key']}] {comment['author']}: {comment['body'][:100]}...")
    
    comments_summary = None
    if all_comments:
        comments_summary = f"Key discussion points from {len(all_comments)} comments analyzed."
    
    return {
        "project_summary": project_summary,
        "feature_areas": feature_areas,
        "cross_cutting_concerns": concerns,
        "technical_context": technical_context,
        "all_comments_summary": comments_summary,
    }


def format_for_llm(context: Dict[str, Any], include_raw_tickets: bool = False) -> str:
    """
    Format aggregated context as markdown text for LLM prompt.
    """
    lines = []
    
    # Project Summary
    ps = context["project_summary"]
    lines.append("## Project Summary")
    lines.append(f"- Total Tickets Analyzed: {ps['total_tickets']}")
    lines.append(f"- Epics: {', '.join(ps['epics']) if ps['epics'] else 'None specified'}")
    lines.append(f"- Issue Types: {ps['issue_type_breakdown']}")
    lines.append(f"- Priority Distribution: {ps['priority_breakdown']}")
    lines.append(f"- Components: {', '.join(ps['components']) if ps['components'] else 'None specified'}")
    lines.append(f"- Labels: {', '.join(ps['labels']) if ps['labels'] else 'None specified'}")
    lines.append("")
    
    # Feature Areas
    lines.append("## Feature Areas")
    for fa in context["feature_areas"]:
        lines.append(f"\n### {fa['epic_key']}: {fa['epic_title']}")
        lines.append(f"- **Priority**: {fa['priority'] or 'Not set'}")
        if fa['description']:
            lines.append(f"- **Description**: {fa['description'][:300]}...")
        
        if fa['stories']:
            lines.append(f"- **Related Tickets** ({len(fa["stories"])}):")
            for story in fa['stories'][:10]:  # Limit to 10
                lines.append(f"  - {story['key']}: {story['summary']} ({story['type']}, {story['priority'] or 'No priority'})")
            if len(fa['stories']) > 10:
                lines.append(f"  - ... and {len(fa['stories']) - 10} more")
        
        if fa['acceptance_criteria']:
            lines.append("- **Acceptance Criteria**:")
            for ac in fa['acceptance_criteria'][:5]:
                lines.append(f"  - {ac}")
        
        if fa['risk_indicators']:
            lines.append(f"- **Risk Indicators**: {', '.join(fa['risk_indicators'])}")
    
    # Cross-Cutting Concerns
    if context["cross_cutting_concerns"]:
        lines.append("\n## Cross-Cutting Concerns Identified")
        for concern in context["cross_cutting_concerns"]:
            lines.append(f"- {concern}")
    
    # Technical Context
    if context["technical_context"]:
        lines.append(f"\n## Technical Context Signals")
        lines.append(context["technical_context"])
    
    # Comments Summary
    if context["all_comments_summary"]:
        lines.append(f"\n## Key Discussion Points")
        lines.append(context["all_comments_summary"])
    
    return "\n".join(lines)
