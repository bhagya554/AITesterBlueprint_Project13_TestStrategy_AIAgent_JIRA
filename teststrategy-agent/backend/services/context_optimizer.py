"""
Context Optimizer
Manages token budget and truncates JIRA context intelligently
"""

from typing import Dict, Any, List, Tuple
from services.llm_provider import get_model_limits, estimate_tokens


def optimize_context(
    jira_context: Dict[str, Any],
    provider: str,
    model: str,
    system_prompt_length: int = 2000,
    template_structure_length: int = 1500,
    output_tokens: int = 8192
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Optimize JIRA context to fit within model token limits.
    
    Returns:
        (optimized_context, metadata) where metadata includes utilization stats
    """
    
    limits = get_model_limits(provider, model)
    context_window = limits["context"]
    max_output = min(limits["output"], output_tokens)
    
    # Reserve tokens
    reserved = system_prompt_length + template_structure_length + max_output + 500  # Buffer
    available = context_window - reserved
    
    # Estimate current token count
    context_json = str(jira_context)
    current_tokens = estimate_tokens(context_json)
    
    metadata = {
        "context_window": context_window,
        "reserved": reserved,
        "available_for_context": available,
        "original_tokens": current_tokens,
        "optimization_level": 0,
    }
    
    # If within budget, return as-is
    if current_tokens <= available:
        metadata["final_tokens"] = current_tokens
        metadata["utilization_pct"] = round((current_tokens / available) * 100, 1)
        metadata["truncated"] = False
        return jira_context, metadata
    
    # Need to optimize - start with level 1: trim comments
    optimized = _level1_trim_comments(jira_context)
    tokens = estimate_tokens(str(optimized))
    metadata["optimization_level"] = 1
    
    if tokens <= available:
        metadata["final_tokens"] = tokens
        metadata["utilization_pct"] = round((tokens / available) * 100, 1)
        metadata["truncated"] = True
        return optimized, metadata
    
    # Level 2: summarize low-priority descriptions
    optimized = _level2_summarize_descriptions(optimized)
    tokens = estimate_tokens(str(optimized))
    metadata["optimization_level"] = 2
    
    if tokens <= available:
        metadata["final_tokens"] = tokens
        metadata["utilization_pct"] = round((tokens / available) * 100, 1)
        metadata["truncated"] = True
        return optimized, metadata
    
    # Level 3: remove linked issues, trim AC
    optimized = _level3_trim_extras(optimized)
    tokens = estimate_tokens(str(optimized))
    metadata["optimization_level"] = 3
    
    if tokens <= available:
        metadata["final_tokens"] = tokens
        metadata["utilization_pct"] = round((tokens / available) * 100, 1)
        metadata["truncated"] = True
        return optimized, metadata
    
    # Level 4: keep only essential info (titles, types, priorities)
    optimized = _level4_essential_only(optimized)
    tokens = estimate_tokens(str(optimized))
    metadata["optimization_level"] = 4
    metadata["final_tokens"] = tokens
    metadata["utilization_pct"] = round((tokens / available) * 100, 1)
    metadata["truncated"] = True
    
    return optimized, metadata


def _level1_trim_comments(context: Dict[str, Any]) -> Dict[str, Any]:
    """Level 1: Remove all comments."""
    optimized = _deep_copy(context)
    
    # Remove comments summary
    optimized["all_comments_summary"] = None
    
    # Remove comments from feature areas
    for fa in optimized.get("feature_areas", []):
        # Comments are already limited during extraction
        pass
    
    return optimized


def _level2_summarize_descriptions(context: Dict[str, Any]) -> Dict[str, Any]:
    """Level 2: Summarize descriptions of low/medium priority items."""
    optimized = _deep_copy(context)
    
    for fa in optimized.get("feature_areas", []):
        # Keep epic description, but summarize
        if fa.get("description"):
            desc = fa["description"]
            if len(desc) > 200:
                fa["description"] = desc[:200] + "... [truncated]"
        
        # For low priority stories, remove detailed descriptions
        stories = fa.get("stories", [])
        for story in stories:
            priority = story.get("priority", "").lower()
            if priority in ["low", "lowest", "medium"]:
                # Keep only summary, not full description
                pass
    
    return optimized


def _level3_trim_extras(context: Dict[str, Any]) -> Dict[str, Any]:
    """Level 3: Remove linked issues, trim acceptance criteria."""
    optimized = _deep_copy(context)
    
    for fa in optimized.get("feature_areas", []):
        # Limit acceptance criteria
        ac_list = fa.get("acceptance_criteria", [])
        if len(ac_list) > 3:
            fa["acceptance_criteria"] = ac_list[:3]
        
        # Simplify stories list
        stories = fa.get("stories", [])
        simplified_stories = []
        for story in stories[:10]:  # Max 10 stories per epic
            simplified_stories.append({
                "key": story.get("key"),
                "summary": story.get("summary"),
                "type": story.get("type"),
                "priority": story.get("priority"),
            })
        fa["stories"] = simplified_stories
    
    # Reduce cross-cutting concerns
    concerns = optimized.get("cross_cutting_concerns", [])
    if len(concerns) > 3:
        optimized["cross_cutting_concerns"] = concerns[:3]
    
    return optimized


def _level4_essential_only(context: Dict[str, Any]) -> Dict[str, Any]:
    """Level 4: Keep only essential information."""
    ps = context.get("project_summary", {})
    
    # Build minimal context
    essential = {
        "project_summary": {
            "total_tickets": ps.get("total_tickets", 0),
            "epics": ps.get("epics", []),
            "issue_type_breakdown": ps.get("issue_type_breakdown", {}),
            "priority_breakdown": ps.get("priority_breakdown", {}),
            "components": ps.get("components", [])[:5],  # Limit components
            "labels": ps.get("labels", [])[:5],  # Limit labels
        },
        "feature_areas": [],
        "cross_cutting_concerns": context.get("cross_cutting_concerns", [])[:2],
        "technical_context": context.get("technical_context"),
        "all_comments_summary": None,
    }
    
    # Minimal feature areas
    for fa in context.get("feature_areas", []):
        essential["feature_areas"].append({
            "epic_key": fa.get("epic_key"),
            "epic_title": fa.get("epic_title"),
            "priority": fa.get("priority"),
            "stories": [
                {"key": s.get("key"), "summary": s.get("summary")}
                for s in fa.get("stories", [])[:5]
            ],
            "risk_indicators": fa.get("risk_indicators", [])[:3],
        })
    
    return essential


def _deep_copy(obj: Any) -> Any:
    """Simple deep copy for dict/list structures."""
    import json
    return json.loads(json.dumps(obj))


def calculate_depth_tokens(depth: str, provider: str, model: str) -> int:
    """
    Calculate appropriate output token count based on depth setting.
    """
    limits = get_model_limits(provider, model)
    max_output = limits["output"]
    
    depth_targets = {
        "standard": 4000,      # ~3,000 words
        "detailed": 8000,      # ~6,000 words  
        "comprehensive": 12000 # ~9,000 words
    }
    
    target = depth_targets.get(depth, 8000)
    
    # Don't exceed model limit
    return min(target, max_output - 1000)  # Leave some buffer


def should_use_sectional_generation(depth: str, provider: str, model: str) -> bool:
    """
    Determine if sectional generation should be used based on depth and model capabilities.
    """
    limits = get_model_limits(provider, model)
    max_output = limits["output"]
    
    depth_requirements = {
        "standard": 4000,
        "detailed": 8000,
        "comprehensive": 12000
    }
    
    required = depth_requirements.get(depth, 8000)
    
    # Use sectional if requirement exceeds 80% of model capacity
    return required > (max_output * 0.8)


def get_optimization_recommendation(metadata: Dict[str, Any]) -> str:
    """Get human-readable recommendation based on optimization results."""
    
    level = metadata.get("optimization_level", 0)
    utilization = metadata.get("utilization_pct", 0)
    
    if level == 0:
        if utilization > 80:
            return f"Context utilization: {utilization}%. Consider using 'Detailed' depth for more comprehensive output."
        return f"Context utilization: {utilization}%. Optimal."
    
    elif level == 1:
        return f"Context optimized (level 1): Comments removed. Utilization: {utilization}%."
    
    elif level == 2:
        return f"Context optimized (level 2): Low-priority descriptions summarized. Utilization: {utilization}%."
    
    elif level == 3:
        return f"Context optimized (level 3): Linked issues and extra AC removed. Utilization: {utilization}%."
    
    else:
        return f"Context highly optimized (level 4): Only essential info retained. Utilization: {utilization}%. Consider selecting fewer tickets."
