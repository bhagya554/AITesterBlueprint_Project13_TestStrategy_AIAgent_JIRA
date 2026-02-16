# SOP: Template Parsing

## Purpose
Extract section structure from test strategy PDF template for LLM guidance.

## Input
- `pdf_path`: Path to test strategy template PDF

## Output
- Hierarchical section structure with numbers, titles, and nesting
- Raw text fallback for failed parsing

## Procedure

### 1. Text Extraction
- Use `pdfplumber.open(pdf_path)`
- Extract text from all pages: `page.extract_text()`

### 2. Section Detection (Hybrid Approach)

#### Primary: Regex Pattern Matching
- Pattern: `^(\d+(?:\.\d+){0,2})\s+([A-Z][A-Za-z\s&\-]+?)$`
- Matches: 1., 1.1, 1.1.1, 2., etc.
- Filter: Length 3-100 chars, not sentences (>15 words)

#### Secondary: Font Analysis (Fallback)
- Check `page.chars` for fontname and size
- Detect bold: `"bold" in char["fontname"].lower()`
- Headings: Larger font size (>14) or bold

### 3. Hierarchy Building
- Parse section numbers to determine depth (dots + 1)
- Use stack-based algorithm to build parent-child relationships
- Root sections: depth=1, Subsections: depth=2, etc.

### 4. Fallback
- If <5 sections detected, use keyword matching
- Common keywords: Introduction, Overview, Approach, Methodology, Automation, etc.
- If all fails, return raw text for LLM interpretation

## Output Format
```json
{
  "sections": [
    {
      "number": "1",
      "title": "Introduction",
      "depth": 1,
      "subsections": [
        {"number": "1.1", "title": "Purpose", "depth": 2, "subsections": []}
      ]
    }
  ],
  "raw_text": "...",
  "total_sections": 13
}
```

## Default Template Structure
If PDF parsing fails entirely, use hardcoded 13-section structure based on `teststrategy.pdf`:
1. Introduction, 2. Project Overview, 3. Test Approach, etc.
