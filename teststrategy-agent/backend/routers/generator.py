"""
Generator API Router
Endpoints for generating test strategies with SSE streaming
"""

import json
import asyncio
import time
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from models import GenerateRequest, SectionRegenerateRequest, ExportRequest
from services.jira_client import fetch_tickets, fetch_children
from services.jira_aggregator import aggregate_tickets, format_for_llm
from services.template_parser import parse_template, find_template_file, get_default_template_structure
from services.llm_provider import get_provider
from services.context_optimizer import should_use_sectional_generation, calculate_depth_tokens
from services.context_optimizer import optimize_context, calculate_depth_tokens as calc_tokens
from services.prompt_builder import build_generation_prompt, build_section_prompt, extract_title_from_content
from services.export_service import generate_pdf, generate_docx
from database import SessionLocal
from database import save_strategy

router = APIRouter(prefix="/api/generate", tags=["generator"])


@router.post("/stream")
async def generate_stream(request: Request, gen_request: GenerateRequest):
    """
    SSE endpoint for streaming test strategy generation.
    """
    async def event_generator():
        start_time = time.time()
        full_content = []
        
        try:
            # Stage 1: Fetch and analyze JIRA context
            yield json.dumps({
                "type": "status",
                "stage": 1,
                "message": f"Analyzing JIRA context ({len(gen_request.jira_ticket_ids)} tickets)..."
            })
            
            tickets, errors = await fetch_tickets(gen_request.jira_ticket_ids)
            
            if not tickets:
                yield json.dumps({
                    "type": "error",
                    "error": "No tickets found or accessible",
                    "code": "NO_TICKETS"
                })
                return
            
            # Fetch children if requested
            if gen_request.fetch_children:
                for ticket in list(tickets):
                    if ticket.get("issue_type") == "Epic":
                        children = await fetch_children(ticket["key"])
                        tickets.extend(children)
            
            # Aggregate context
            jira_context = aggregate_tickets(tickets)
            
            if errors:
                yield json.dumps({
                    "type": "warning",
                    "message": f"Fetched {len(tickets)} tickets with {len(errors)} errors: {', '.join(errors[:3])}"
                })
            
            # Stage 2: Parse template
            yield json.dumps({
                "type": "status",
                "stage": 2,
                "message": "Parsing template structure..."
            })
            
            template_path = find_template_file()
            if template_path:
                template_result = parse_template(template_path)
                if template_result.get("success"):
                    template_sections = template_result.get("sections", [])
                else:
                    template_sections = get_default_template_structure()
            else:
                template_sections = get_default_template_structure()
            
            # Stage 3: Optimize context
            provider = get_provider(gen_request.provider.value)
            output_tokens = calc_tokens(gen_request.depth, gen_request.provider.value, gen_request.model)
            
            optimized_context, metadata = optimize_context(
                jira_context,
                gen_request.provider.value,
                gen_request.model,
                output_tokens=output_tokens
            )
            
            yield json.dumps({
                "type": "status",
                "stage": 3,
                "message": f"Generating test strategy (utilization: {metadata.get('utilization_pct', 0):.0f}%)..."
            })
            
            # Determine generation mode
            use_sectional = should_use_sectional_generation(
                gen_request.depth,
                gen_request.provider.value,
                gen_request.model
            )
            
            focus_areas = [fa.value for fa in gen_request.focus_areas]
            
            if use_sectional:
                # Generate section by section
                previous_content = ""
                
                for section in template_sections:
                    section_title = section.get("title", "")
                    section_number = section.get("number", "")
                    
                    yield json.dumps({
                        "type": "section_start",
                        "section": section_title,
                        "section_number": section_number
                    })
                    
                    prompt = build_section_prompt(
                        section=section,
                        template_sections=template_sections,
                        jira_context=optimized_context,
                        depth=gen_request.depth.value,
                        focus_areas=focus_areas,
                        previous_content=previous_content,
                        additional_context=gen_request.additional_context
                    )
                    
                    section_content = []
                    async for chunk in provider.generate_stream(
                        prompt=prompt,
                        system_prompt="You are a Principal QA Architect generating test strategy documents.",
                        model=gen_request.model,
                        temperature=gen_request.temperature,
                        max_tokens=output_tokens // len(template_sections)
                    ):
                        section_content.append(chunk)
                        yield json.dumps({
                            "type": "content",
                            "text": chunk
                        })
                    
                    full_content.append("".join(section_content))
                    previous_content = "\n\n".join(full_content)
                    
                    yield json.dumps({
                        "type": "section_complete",
                        "section": section_title
                    })
            else:
                # Generate all at once
                prompt = build_generation_prompt(
                    template_sections=template_sections,
                    jira_context=optimized_context,
                    depth=gen_request.depth.value,
                    focus_areas=focus_areas,
                    additional_context=gen_request.additional_context
                )
                
                async for chunk in provider.generate_stream(
                    prompt=prompt,
                    system_prompt="You are a Principal QA Architect generating test strategy documents.",
                    model=gen_request.model,
                    temperature=gen_request.temperature,
                    max_tokens=output_tokens
                ):
                    full_content.append(chunk)
                    yield json.dumps({
                        "type": "content",
                        "text": chunk
                    })
            
            # Done
            generation_time = time.time() - start_time
            final_content = "".join(full_content)
            
            yield json.dumps({
                "type": "done",
                "total_tokens_used": len(final_content) // 4,  # Rough estimate
                "generation_time_seconds": round(generation_time, 2)
            })
            
        except Exception as e:
            error_str = str(e).lower()
            error_code = "UNKNOWN"
            
            if "rate limit" in error_str:
                error_code = "RATE_LIMIT"
            elif "authentication" in error_str or "401" in error_str:
                error_code = "AUTH"
            elif "context" in error_str and "length" in error_str:
                error_code = "CONTEXT_LENGTH"
            elif "connection" in error_str:
                error_code = "CONNECTION"
            
            yield json.dumps({
                "type": "error",
                "error": str(e),
                "code": error_code
            })
    
    return EventSourceResponse(event_generator())


@router.post("/section")
async def regenerate_section(request: SectionRegenerateRequest):
    """Regenerate a specific section."""
    try:
        provider = get_provider(request.provider.value)
        
        prompt = build_section_prompt(
            section={"number": request.section_number, "title": request.section_title, "subsections": []},
            template_sections=[],  # Not needed for single section
            jira_context=request.jira_context.model_dump(),
            depth="detailed",
            focus_areas=[],
            previous_content=request.previous_content
        )
        
        chunks = []
        async for chunk in provider.generate_stream(
            prompt=prompt,
            system_prompt="You are a Principal QA Architect. Regenerate only the requested section.",
            model=request.model,
            temperature=request.temperature,
            max_tokens=4000
        ):
            chunks.append(chunk)
        
        return {
            "success": True,
            "content": "".join(chunks)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/pdf")
async def export_pdf(request: ExportRequest):
    """Export strategy as PDF."""
    try:
        pdf_bytes = generate_pdf(
            content=request.content,
            title=request.title,
            project_name=request.project_name,
            classification=request.classification
        )
        
        from fastapi.responses import Response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{request.title.replace(" ", "_")}.pdf"'
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.post("/export/docx")
async def export_docx(request: ExportRequest):
    """Export strategy as DOCX."""
    try:
        docx_bytes = generate_docx(
            content=request.content,
            title=request.title,
            project_name=request.project_name,
            classification=request.classification
        )
        
        from fastapi.responses import Response
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{request.title.replace(" ", "_")}.docx"'
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DOCX generation failed: {str(e)}")
