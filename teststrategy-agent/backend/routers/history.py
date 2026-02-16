"""
History API Router
Endpoints for managing saved test strategies
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db, get_strategy, get_strategies, delete_strategy, save_strategy
from models import StrategyHistoryList, StrategyDetail

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=StrategyHistoryList)
async def list_strategies(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    provider: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List saved test strategies with pagination and filtering."""
    strategies, total = get_strategies(db, skip=skip, limit=limit, search=search, provider=provider)
    
    return StrategyHistoryList(
        items=[s.to_dict() for s in strategies],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{strategy_id}", response_model=StrategyDetail)
async def get_strategy_detail(strategy_id: int, db: Session = Depends(get_db)):
    """Get a specific saved strategy."""
    strategy = get_strategy(db, strategy_id)
    
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    return StrategyDetail(**strategy.to_dict())


@router.delete("/{strategy_id}")
async def delete_strategy_item(strategy_id: int, db: Session = Depends(get_db)):
    """Delete a saved strategy."""
    success = delete_strategy(db, strategy_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    return {"success": True, "message": "Strategy deleted"}


@router.post("/{strategy_id}/clone")
async def clone_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Clone a strategy's settings for re-generation."""
    strategy = get_strategy(db, strategy_id)
    
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    import json
    
    return {
        "success": True,
        "settings": {
            "jira_ticket_ids": strategy.jira_ids.split(","),
            "provider": strategy.provider,
            "model": strategy.model,
            "depth": strategy.depth,
            "focus_areas": json.loads(strategy.focus_areas),
            "temperature": strategy.temperature,
        }
    }
