"""
JIRA API Router
Endpoints for fetching and managing JIRA tickets
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import JiraTicketRequest, JiraTicketsRequest, JiraFetchResponse, JiraTicket
from services.jira_client import fetch_ticket, fetch_tickets, fetch_children, test_connection
from services.jira_aggregator import aggregate_tickets

router = APIRouter(prefix="/api/jira", tags=["jira"])


@router.get("/ticket/{ticket_id}", response_model=JiraTicket)
async def get_ticket(ticket_id: str, fetch_children_flag: bool = True):
    """Fetch a single JIRA ticket by ID."""
    try:
        ticket = await fetch_ticket(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
        
        # Fetch children if requested and ticket is an Epic
        if fetch_children_flag and ticket.get("issue_type") == "Epic":
            children = await fetch_children(ticket_id)
            # You might want to return children separately or include them
            
        return JiraTicket(**ticket)
        
    except HTTPException:
        raise
    except Exception as e:
        error_str = str(e).lower()
        if "401" in error_str or "authentication" in error_str:
            raise HTTPException(status_code=401, detail="JIRA authentication failed. Check credentials in Settings.")
        elif "404" in error_str:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
        elif "connection" in error_str:
            raise HTTPException(status_code=503, detail="Cannot connect to JIRA server")
        else:
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/tickets", response_model=JiraFetchResponse)
async def get_multiple_tickets(request: JiraTicketsRequest):
    """Fetch multiple JIRA tickets."""
    try:
        tickets, errors = await fetch_tickets(request.ticket_ids)
        
        return JiraFetchResponse(
            success=len(tickets) > 0,
            tickets=tickets,
            errors=errors,
            total_fetched=len(tickets),
            total_requested=len(request.ticket_ids)
        )
        
    except Exception as e:
        error_str = str(e).lower()
        if "401" in error_str:
            raise HTTPException(status_code=401, detail="JIRA authentication failed")
        elif "connection" in error_str:
            raise HTTPException(status_code=503, detail="Cannot connect to JIRA server")
        else:
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/ticket/{ticket_id}/children")
async def get_ticket_children(ticket_id: str):
    """Fetch all child issues of a ticket (for epics)."""
    try:
        children = await fetch_children(ticket_id)
        return {
            "parent_key": ticket_id,
            "children_count": len(children),
            "children": children
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-connection")
async def test_jira_connection():
    """Test JIRA connection and return user info."""
    try:
        result = await test_connection()
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=401, detail=result.get("message", "Connection failed"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/aggregate")
async def aggregate_jira_context(request: JiraTicketsRequest):
    """Fetch tickets and return aggregated context."""
    try:
        tickets, errors = await fetch_tickets(request.ticket_ids)
        
        if not tickets:
            raise HTTPException(status_code=404, detail="No tickets found")
        
        # Fetch children for epics if requested
        if request.fetch_children:
            for ticket in tickets:
                if ticket.get("issue_type") == "Epic":
                    children = await fetch_children(ticket["key"])
                    tickets.extend(children)
        
        # Aggregate context
        aggregated = aggregate_tickets(tickets)
        
        return {
            "success": True,
            "aggregated_context": aggregated,
            "errors": errors,
            "total_tickets": len(tickets)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
