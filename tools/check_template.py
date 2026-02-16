#!/usr/bin/env python3
"""
Template PDF Check Tool
Verifies the test strategy template PDF exists and can be parsed
Usage: python tools/check_template.py
"""

import os
import sys
import re
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)


def find_template():
    """Find the template PDF file."""
    
    # Check .env path first
    template_path = os.getenv("TEMPLATE_PATH", "")
    
    if template_path and os.path.exists(template_path):
        return os.path.abspath(template_path)
    
    # Check common locations
    possible_paths = [
        "teststrategy.pdf",
        "./teststrategy.pdf",
        "../teststrategy.pdf",
        os.path.join(os.path.dirname(__file__), "..", "teststrategy.pdf"),
        os.path.join(os.path.dirname(__file__), "..", "..", "teststrategy.pdf"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return os.path.abspath(path)
    
    return None


def parse_template_hybrid(pdf_path: str):
    """Parse PDF template using hybrid regex + font analysis."""
    
    try:
        import pdfplumber
    except ImportError:
        print("❌ pdfplumber not installed")
        print("   Run: pip install pdfplumber")
        return None
    
    print(f"📖 Opening PDF: {pdf_path}")
    
    sections = []
    full_text = ""
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"   Pages: {len(pdf.pages)}")
        
        # Extract all text
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        
        # Regex-based section detection
        # Pattern matches: 1., 1.1, 1.1.1, 2., etc. followed by text
        section_pattern = re.compile(
            r'^(\d+(?:\.\d+){0,2})\s+([A-Z][A-Za-z\s&\-]+)$',
            re.MULTILINE
        )
        
        for match in section_pattern.finditer(full_text):
            number = match.group(1)
            title = match.group(2).strip()
            
            # Filter out likely false positives
            if len(title) < 3 or len(title) > 100:
                continue
            
            depth = number.count('.') + 1
            
            sections.append({
                "number": number,
                "title": title,
                "depth": depth
            })
    
    return sections, full_text


def build_hierarchy(flat_sections):
    """Build section hierarchy from flat list."""
    
    if not flat_sections:
        return []
    
    root = []
    stack = []
    
    for section in flat_sections:
        depth = section["depth"]
        
        # Pop stack until we find the parent
        while stack and stack[-1]["depth"] >= depth:
            stack.pop()
        
        # Create node with subsections
        node = {
            **section,
            "subsections": []
        }
        
        if stack:
            stack[-1]["subsections"].append(node)
        else:
            root.append(node)
        
        stack.append(node)
    
    return root


def print_hierarchy(sections, indent=0):
    """Print section hierarchy."""
    for section in sections:
        prefix = "  " * indent
        print(f"{prefix}{section['number']} {section['title']}")
        if section.get("subsections"):
            print_hierarchy(section["subsections"], indent + 1)


def check_template():
    """Main check function."""
    
    template_path = find_template()
    
    if not template_path:
        print("❌ Template PDF not found!")
        print("\n   Expected locations:")
        print("     - ./teststrategy.pdf (project root)")
        print("     - Path specified in TEMPLATE_PATH env var")
        print("\n   Please place your teststrategy.pdf in the project root")
        print("   or set TEMPLATE_PATH in .env")
        return False
    
    print(f"✅ Template found: {template_path}")
    
    # Parse template
    result = parse_template_hybrid(template_path)
    
    if result is None:
        return False
    
    sections, full_text = result
    
    if not sections:
        print("\n⚠️  Warning: No sections detected in PDF")
        print("   Will use raw text as fallback")
        print(f"\n   Total text length: {len(full_text)} characters")
        return True
    
    print(f"\n✅ Parsed {len(sections)} sections")
    
    # Build and display hierarchy
    hierarchy = build_hierarchy(sections)
    
    print("\n📋 Template Structure:")
    print("-" * 50)
    print_hierarchy(hierarchy)
    print("-" * 50)
    
    # Check for expected test strategy sections
    expected_keywords = [
        "introduction", "overview", "approach", "methodology",
        "automation", "environment", "defect", "risk",
        "criteria", "metrics", "roles", "schedule"
    ]
    
    found_keywords = []
    text_lower = full_text.lower()
    
    for keyword in expected_keywords:
        if keyword in text_lower:
            found_keywords.append(keyword)
    
    print(f"\n✅ Found {len(found_keywords)}/{len(expected_keywords)} expected section keywords")
    
    # Summary
    print("\n📊 Summary:")
    print(f"   • File: {os.path.basename(template_path)}")
    print(f"   • Size: {os.path.getsize(template_path):,} bytes")
    print(f"   • Text length: {len(full_text):,} characters")
    print(f"   • Sections detected: {len(sections)}")
    
    return True


if __name__ == "__main__":
    print("=" * 50)
    print("Template PDF Check Tool")
    print("=" * 50)
    
    success = check_template()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ Template check passed!")
        print("=" * 50)
        sys.exit(0)
    else:
        print("\n" + "=" * 50)
        print("❌ Template check failed.")
        print("=" * 50)
        sys.exit(1)
