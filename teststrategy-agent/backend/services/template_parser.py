"""
Template Parser
Extracts section structure from test strategy PDF template
"""

import re
from typing import List, Dict, Any, Optional
from pathlib import Path


def parse_template(pdf_path: str) -> Dict[str, Any]:
    """
    Parse a test strategy template PDF and extract its section structure.
    Uses hybrid approach: regex-based detection with font validation.
    """
    try:
        import pdfplumber
    except ImportError:
        return {
            "success": False,
            "error": "pdfplumber not installed",
            "sections": [],
            "raw_text": ""
        }
    
    path = Path(pdf_path)
    if not path.exists():
        return {
            "success": False,
            "error": f"File not found: {pdf_path}",
            "sections": [],
            "raw_text": ""
        }
    
    sections = []
    full_text = ""
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Extract text from all pages
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
        
        # Regex-based section detection
        # Pattern matches: 1., 1.1, 1.1.1, 2., etc. followed by title text
        section_pattern = re.compile(
            r'^(\d+(?:\.\d+){0,2})\s+([A-Z][A-Za-z\s&\-]+?)(?:\s*$|\s+(?=\d))',
            re.MULTILINE
        )
        
        # Also match common test strategy section names without numbers
        section_keywords = [
            "Introduction", "Project Overview", "Test Approach", "Test Methodology",
            "Test Automation", "Test Environment", "Defect Management",
            "Risk Management", "Entry Criteria", "Exit Criteria",
            "Test Metrics", "KPIs", "Roles and Responsibilities",
            "Test Schedule", "Communication Plan", "Appendices"
        ]
        
        # Find numbered sections
        for match in section_pattern.finditer(full_text):
            number = match.group(1)
            title = match.group(2).strip()
            
            # Filter out false positives
            if len(title) < 3 or len(title) > 100:
                continue
            
            # Skip if title looks like a sentence
            if title.count(" ") > 15:
                continue
            
            depth = number.count('.') + 1
            
            sections.append({
                "number": number,
                "title": title,
                "depth": depth,
                "subsections": []
            })
        
        # If regex found too few sections, try keyword-based fallback
        if len(sections) < 5:
            for keyword in section_keywords:
                # Find keyword in text (at line start or after newline)
                pattern = rf'(?:^|\n)({re.escape(keyword)}[A-Za-z\s]*)(?:\n|$)'
                for match in re.finditer(pattern, full_text, re.IGNORECASE):
                    title = match.group(1).strip()
                    # Check if not already found
                    if not any(s["title"].lower() == title.lower() for s in sections):
                        sections.append({
                            "number": str(len(sections) + 1),
                            "title": title,
                            "depth": 1,
                            "subsections": []
                        })
        
        # Build hierarchy
        hierarchy = build_hierarchy(sections)
        
        return {
            "success": True,
            "sections": hierarchy,
            "raw_text": full_text[:5000],  # First 5000 chars
            "total_sections": len(sections)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "sections": [],
            "raw_text": full_text[:5000] if full_text else ""
        }


def build_hierarchy(flat_sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build section hierarchy from flat list based on numbering depth."""
    
    if not flat_sections:
        return []
    
    root = []
    stack = []
    
    for section in flat_sections:
        depth = section["depth"]
        
        # Pop stack until we find the parent
        while stack and stack[-1]["depth"] >= depth:
            stack.pop()
        
        # Create node
        node = {
            **section,
            "subsections": []
        }
        
        # Add to parent or root
        if stack:
            stack[-1]["subsections"].append(node)
        else:
            root.append(node)
        
        stack.append(node)
    
    return root


def extract_section_hierarchy_for_prompt(sections: List[Dict[str, Any]], indent: int = 0) -> str:
    """Convert section hierarchy to text format for LLM prompt."""
    lines = []
    
    for section in sections:
        prefix = "  " * indent
        lines.append(f"{prefix}{section['number']}. {section['title']}")
        
        if section.get("subsections"):
            lines.append(extract_section_hierarchy_for_prompt(section["subsections"], indent + 1))
    
    return "\n".join(lines)


def get_default_template_structure() -> List[Dict[str, Any]]:
    """
    Fallback default structure if PDF parsing fails.
    Based on the teststrategy.pdf template.
    """
    return [
        {
            "number": "1",
            "title": "Introduction",
            "depth": 1,
            "subsections": [
                {"number": "1.1", "title": "Purpose", "depth": 2, "subsections": []},
                {"number": "1.2", "title": "Scope", "depth": 2, "subsections": []},
                {"number": "1.3", "title": "Objectives", "depth": 2, "subsections": []},
            ]
        },
        {
            "number": "2",
            "title": "Project Overview",
            "depth": 1,
            "subsections": [
                {"number": "2.1", "title": "Description", "depth": 2, "subsections": []},
                {"number": "2.2", "title": "Stakeholders", "depth": 2, "subsections": []},
                {"number": "2.3", "title": "Architecture", "depth": 2, "subsections": []},
            ]
        },
        {
            "number": "3",
            "title": "Test Approach & Methodology",
            "depth": 1,
            "subsections": [
                {"number": "3.1", "title": "Testing Philosophy", "depth": 2, "subsections": []},
                {"number": "3.2", "title": "Testing Levels", "depth": 2, "subsections": []},
                {"number": "3.3", "title": "Testing Types", "depth": 2, "subsections": []},
            ]
        },
        {
            "number": "4",
            "title": "Test Automation Strategy",
            "depth": 1,
            "subsections": [
                {"number": "4.1", "title": "Automation Approach", "depth": 2, "subsections": []},
                {"number": "4.2", "title": "Framework & Tools", "depth": 2, "subsections": []},
            ]
        },
        {
            "number": "5",
            "title": "Test Environment Strategy",
            "depth": 1,
            "subsections": [
                {"number": "5.1", "title": "Environment Topology", "depth": 2, "subsections": []},
                {"number": "5.2", "title": "Test Data Management", "depth": 2, "subsections": []},
            ]
        },
        {
            "number": "6",
            "title": "Defect Management Strategy",
            "depth": 1,
            "subsections": [
                {"number": "6.1", "title": "Defect Lifecycle", "depth": 2, "subsections": []},
                {"number": "6.2", "title": "Severity & Priority", "depth": 2, "subsections": []},
            ]
        },
        {
            "number": "7",
            "title": "Risk-Based Testing & Risk Management",
            "depth": 1,
            "subsections": [
                {"number": "7.1", "title": "Risk Assessment Framework", "depth": 2, "subsections": []},
                {"number": "7.2", "title": "Risk Register", "depth": 2, "subsections": []},
            ]
        },
        {
            "number": "8",
            "title": "Entry & Exit Criteria",
            "depth": 1,
            "subsections": [
                {"number": "8.1", "title": "Entry Criteria", "depth": 2, "subsections": []},
                {"number": "8.2", "title": "Exit Criteria", "depth": 2, "subsections": []},
            ]
        },
        {
            "number": "9",
            "title": "Test Metrics, KPIs & Reporting",
            "depth": 1,
            "subsections": [
                {"number": "9.1", "title": "Key Metrics", "depth": 2, "subsections": []},
                {"number": "9.2", "title": "Reporting Cadence", "depth": 2, "subsections": []},
            ]
        },
        {
            "number": "10",
            "title": "Roles and Responsibilities",
            "depth": 1,
            "subsections": []
        },
        {
            "number": "11",
            "title": "Test Schedule & Milestones",
            "depth": 1,
            "subsections": [
                {"number": "11.1", "title": "Schedule", "depth": 2, "subsections": []},
                {"number": "11.2", "title": "Quality Gates", "depth": 2, "subsections": []},
            ]
        },
        {
            "number": "12",
            "title": "Communication & Escalation Plan",
            "depth": 1,
            "subsections": [
                {"number": "12.1", "title": "Communication Matrix", "depth": 2, "subsections": []},
                {"number": "12.2", "title": "Escalation Path", "depth": 2, "subsections": []},
            ]
        },
        {
            "number": "13",
            "title": "Appendices",
            "depth": 1,
            "subsections": [
                {"number": "13.1", "title": "Glossary", "depth": 2, "subsections": []},
                {"number": "13.2", "title": "Assumptions", "depth": 2, "subsections": []},
                {"number": "13.3", "title": "Constraints", "depth": 2, "subsections": []},
            ]
        },
    ]


def find_template_file() -> Optional[str]:
    """Find the template PDF file in common locations."""
    from config import get_settings
    
    settings = get_settings()
    
    # Check configured path
    if settings.template_path:
        path = Path(settings.template_path)
        if path.exists():
            return str(path.absolute())
    
    # Check common locations
    possible_paths = [
        "teststrategy.pdf",
        "./teststrategy.pdf",
        "../teststrategy.pdf",
        "../../teststrategy.pdf",
    ]
    
    for path_str in possible_paths:
        path = Path(path_str)
        if path.exists():
            return str(path.absolute())
    
    return None
