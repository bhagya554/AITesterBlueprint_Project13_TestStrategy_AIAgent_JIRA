"""
Prompt Builder
Constructs LLM prompts for test strategy generation
"""

from typing import Dict, Any, List, Optional
from services.template_parser import extract_section_hierarchy_for_prompt


SYSTEM_PROMPT = """You are a Principal QA Architect and Test Strategist with 20+ years of experience in enterprise software quality assurance across industries including fintech, healthcare, e-commerce, and SaaS.

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

2. Fill EVERY section of the template with substantive, project-specific content. Never leave a section with just placeholder text or generic boilerplate.

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

6. Maintain internal consistency — if you mention a tool in Section 4, reference it again in Section 5 (environments) and Section 9 (reporting).

7. Format output in clean Markdown with proper heading hierarchy matching the template. Use tables where the template uses tables. Use bullet points sparingly and meaningfully.
"""


DEPTH_INSTRUCTIONS = {
    "standard": """Generate a focused test strategy covering all template sections with moderate detail.
Each major section should be 200-400 words. Total output: ~3,000-5,000 words.
Be concise but comprehensive. Focus on key decisions and rationale.""",
    
    "detailed": """Generate a thorough test strategy with specific examples and detailed recommendations.
Each major section should be 400-700 words. Include specific tool configurations,
sample metrics calculations, and detailed risk analysis. Total output: ~5,000-8,000 words.""",
    
    "comprehensive": """Generate an exhaustive test strategy suitable for enterprise governance review.
Each major section should be 600-1000 words. Include worked examples, sample
test case outlines for critical areas, detailed RACI matrix, specific SLA
calculations, tool comparison rationale, and appendices with supporting detail.
Total output: ~8,000-12,000 words."""
}


def build_generation_prompt(
    template_sections: List[Dict[str, Any]],
    jira_context: Dict[str, Any],
    depth: str,
    focus_areas: List[str],
    additional_context: Optional[str] = None,
    previous_sections: Optional[str] = None
) -> str:
    """
    Build the main generation prompt.
    
    Args:
        template_sections: Parsed template hierarchy
        jira_context: Aggregated JIRA context
        depth: Strategy depth (standard/detailed/comprehensive)
        focus_areas: List of focus areas to emphasize
        additional_context: Optional user-provided context
        previous_sections: Previously generated sections (for sectional generation)
    """
    
    lines = []
    
    # Depth instruction
    lines.append(DEPTH_INSTRUCTIONS.get(depth, DEPTH_INSTRUCTIONS["detailed"]))
    lines.append("")
    
    # Template structure
    lines.append("## TEST STRATEGY TEMPLATE STRUCTURE")
    lines.append("Follow this exact structure for your response:")
    lines.append("")
    lines.append(extract_section_hierarchy_for_prompt(template_sections))
    lines.append("")
    
    # Previous sections context (for sectional generation)
    if previous_sections:
        lines.append("## PREVIOUSLY GENERATED SECTIONS")
        lines.append("For consistency, reference these sections where relevant:")
        lines.append("")
        lines.append(previous_sections[:2000])  # Limit context
        lines.append("")
    
    # JIRA Context
    lines.append("## JIRA PROJECT CONTEXT")
    lines.append("")
    
    # Project Summary
    ps = jira_context.get("project_summary", {})
    lines.append("### Project Summary")
    lines.append(f"- **Total Tickets Analyzed**: {ps.get('total_tickets', 0)}")
    lines.append(f"- **Epics**: {', '.join(ps.get('epics', [])) or 'None specified'}")
    
    issue_breakdown = ps.get('issue_type_breakdown', {})
    if issue_breakdown:
        lines.append(f"- **Issue Types**: {issue_breakdown}")
    
    priority_breakdown = ps.get('priority_breakdown', {})
    if priority_breakdown:
        lines.append(f"- **Priority Distribution**: {priority_breakdown}")
    
    components = ps.get('components', [])
    if components:
        lines.append(f"- **Components**: {', '.join(components)}")
    
    labels = ps.get('labels', [])
    if labels:
        lines.append(f"- **Labels**: {', '.join(labels)}")
    
    lines.append("")
    
    # Feature Areas
    lines.append("### Feature Areas")
    for fa in jira_context.get("feature_areas", []):
        lines.append(f"\n#### {fa.get('epic_key', 'Unknown')}: {fa.get('epic_title', '')}")
        lines.append(f"- **Priority**: {fa.get('priority') or 'Not set'}")
        
        if fa.get('description'):
            desc = fa['description'][:300] + "..." if len(fa['description']) > 300 else fa['description']
            lines.append(f"- **Description**: {desc}")
        
        stories = fa.get('stories', [])
        if stories:
            lines.append(f"- **Related Tickets** ({len(stories)}):")
            for story in stories[:8]:  # Limit to 8
                lines.append(f"  - {story.get('key')}: {story.get('summary')} ({story.get('type')}, {story.get('priority') or 'No priority'})")
            if len(stories) > 8:
                lines.append(f"  - ... and {len(stories) - 8} more")
        
        ac_list = fa.get('acceptance_criteria', [])
        if ac_list:
            lines.append("- **Acceptance Criteria**:")
            for ac in ac_list[:3]:  # Limit to 3
                lines.append(f"  - {ac[:100]}...")
        
        risks = fa.get('risk_indicators', [])
        if risks:
            lines.append(f"- **Risk Indicators**: {', '.join(risks[:5])}")
    
    lines.append("")
    
    # Cross-Cutting Concerns
    concerns = jira_context.get("cross_cutting_concerns", [])
    if concerns:
        lines.append("### Cross-Cutting Concerns Identified")
        for concern in concerns:
            lines.append(f"- {concern}")
        lines.append("")
    
    # Technical Context
    tech_context = jira_context.get("technical_context")
    if tech_context:
        lines.append("### Technical Context Signals")
        lines.append(tech_context)
        lines.append("")
    
    # Focus Areas
    if focus_areas:
        lines.append("### User-Selected Focus Areas")
        lines.append("Emphasize these areas in your strategy:")
        for area in focus_areas:
            lines.append(f"- ☑ {area.replace('_', ' ').title()}")
        lines.append("")
    
    # Additional Context
    if additional_context:
        lines.append("### Additional Context Provided by User")
        lines.append(additional_context)
        lines.append("")
    
    # Final instruction
    lines.append("---")
    lines.append("")
    lines.append("Generate the complete Test Strategy document now, following the template structure exactly.")
    lines.append("Ensure every section is populated with project-specific, actionable content derived from")
    lines.append("the JIRA context above. Do not include placeholder text like '[fill in]' — instead, make")
    lines.append("informed recommendations based on the available context and note your assumptions.")
    
    return "\n".join(lines)


def build_section_prompt(
    section: Dict[str, Any],
    template_sections: List[Dict[str, Any]],
    jira_context: Dict[str, Any],
    depth: str,
    focus_areas: List[str],
    previous_content: str,
    additional_context: Optional[str] = None
) -> str:
    """
    Build a prompt for generating a single section (sectional generation mode).
    """
    
    lines = []
    
    lines.append(DEPTH_INSTRUCTIONS.get(depth, DEPTH_INSTRUCTIONS["detailed"]))
    lines.append("")
    
    lines.append(f"## SECTION TO GENERATE: {section['number']}. {section['title']}")
    lines.append("")
    
    if section.get('subsections'):
        lines.append("This section includes the following subsections:")
        for sub in section['subsections']:
            lines.append(f"- {sub['number']}. {sub['title']}")
        lines.append("")
    
    lines.append("## FULL TEMPLATE STRUCTURE (for context)")
    lines.append(extract_section_hierarchy_for_prompt(template_sections))
    lines.append("")
    
    lines.append("## PREVIOUSLY GENERATED CONTENT (for consistency)")
    lines.append(previous_content[-3000:] if len(previous_content) > 3000 else previous_content)
    lines.append("")
    
    lines.append("## PROJECT CONTEXT")
    ps = jira_context.get("project_summary", {})
    lines.append(f"- Total Tickets: {ps.get('total_tickets', 0)}")
    lines.append(f"- Epics: {', '.join(ps.get('epics', [])[:3])}")
    lines.append(f"- Issue Types: {ps.get('issue_type_breakdown', {})}")
    lines.append("")
    
    if focus_areas:
        lines.append(f"- Focus Areas: {', '.join(focus_areas)}")
        lines.append("")
    
    if additional_context:
        lines.append("## Additional Context")
        lines.append(additional_context)
        lines.append("")
    
    lines.append("---")
    lines.append(f"Generate ONLY section {section['number']}. {section['title']} now.")
    lines.append("Maintain consistency with previously generated content.")
    lines.append("Use proper Markdown formatting with appropriate heading levels.")
    
    return "\n".join(lines)


def extract_title_from_content(content: str, jira_context: Dict[str, Any]) -> str:
    """Extract a title for the strategy from content or JIRA context."""
    
    # Try to get from epics
    epics = jira_context.get("project_summary", {}).get("epics", [])
    if epics:
        # Extract project name from first epic
        epic = epics[0]
        if ":" in epic:
            return f"Test Strategy: {epic.split(':', 1)[1].strip()}"
        return f"Test Strategy: {epic}"
    
    # Default title
    return "Test Strategy Document"
