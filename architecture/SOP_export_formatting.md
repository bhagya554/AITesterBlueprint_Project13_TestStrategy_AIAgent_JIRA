# SOP: Export Formatting (PDF & DOCX)

## Purpose
Generate professionally formatted documents from markdown content.

## Input
- Markdown content
- Title, project name, classification
- Optional: company name, logo

## Output
- PDF or DOCX file bytes

## PDF Export (ReportLab)

### Cover Page
- Company name (if configured)
- Title: "Test Strategy Document"
- Project name
- Date, version, classification

### Document Structure
- Heading 1: #1B3A5C (navy)
- Heading 2: #2E75B6 (primary blue)
- Heading 3: #2E75B6
- Body: Calibri/Helvetica, 10pt
- Line spacing: 1.15

### Tables
- Header row: Light gray background
- Border: Thin gray lines
- Cell padding: 4pt

### Headers/Footers
- Header: "Test Strategy Document | {Project}"
- Footer: "{Classification} | Page X of Y"

## DOCX Export (python-docx)

### Styles Applied
- Title: Title style, 24pt, centered
- Heading 1: Heading 1, navy color
- Heading 2: Heading 2, blue color
- Heading 3: Heading 3
- Body: Normal, justified
- Lists: List Bullet / List Number

### Formatting
- Font: Calibri (11pt)
- Margins: Normal (1 inch)
- Page breaks: Before major sections

## Markdown to Document Conversion

### Headers
```python
# H1 -> Heading 1
## H2 -> Heading 2
### H3 -> Heading 3
```

### Text Formatting
```python
**bold** -> Bold run
*italic* -> Italic run
`code` -> Courier font
```

### Lists
```python
- item -> List Bullet
1. item -> List Number
```

### Tables
- Parse | delimited rows
- First row = header (bold, shaded)
- Create Table object with appropriate columns

## Error Handling
- Missing package: Clear install instruction
- Content too long: Truncate with warning
- Invalid characters: Escape or remove
