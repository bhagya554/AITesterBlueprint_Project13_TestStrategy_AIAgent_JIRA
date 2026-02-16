"""
Database Models and Session Management
SQLite with SQLAlchemy
"""

import os
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, String, Text, Integer, Float, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session


class Base(DeclarativeBase):
    pass


class StrategyHistory(Base):
    """Saved test strategies."""
    __tablename__ = "strategy_history"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    jira_ids: Mapped[str] = mapped_column(String(1000), nullable=False)  # Comma-separated
    project_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Generation settings
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    depth: Mapped[str] = mapped_column(String(50), nullable=False)  # standard/detailed/comprehensive
    focus_areas: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array
    temperature: Mapped[float] = mapped_column(Float, default=0.3)
    
    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Markdown content
    template_structure: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    
    # Metadata
    total_tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    generation_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "jira_ids": self.jira_ids,
            "project_name": self.project_name,
            "provider": self.provider,
            "model": self.model,
            "depth": self.depth,
            "focus_areas": self.focus_areas,
            "temperature": self.temperature,
            "content": self.content,
            "template_structure": self.template_structure,
            "total_tokens_used": self.total_tokens_used,
            "generation_time_seconds": self.generation_time_seconds,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SettingsStore(Base):
    """Additional settings stored in DB (beyond .env)."""
    __tablename__ = "settings_store"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./teststrategy.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session (for FastAPI dependency)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_strategy(
    db: Session,
    title: str,
    jira_ids: List[str],
    provider: str,
    model: str,
    depth: str,
    focus_areas: List[str],
    temperature: float,
    content: str,
    template_structure: Optional[dict] = None,
    project_name: Optional[str] = None,
    total_tokens_used: Optional[int] = None,
    generation_time_seconds: Optional[float] = None,
) -> StrategyHistory:
    """Save a generated strategy to history."""
    
    import json
    
    strategy = StrategyHistory(
        title=title,
        jira_ids=",".join(jira_ids),
        project_name=project_name,
        provider=provider,
        model=model,
        depth=depth,
        focus_areas=json.dumps(focus_areas),
        temperature=temperature,
        content=content,
        template_structure=json.dumps(template_structure) if template_structure else None,
        total_tokens_used=total_tokens_used,
        generation_time_seconds=generation_time_seconds,
    )
    
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return strategy


def get_strategy(db: Session, strategy_id: int) -> Optional[StrategyHistory]:
    """Get a strategy by ID."""
    return db.query(StrategyHistory).filter(StrategyHistory.id == strategy_id).first()


def get_strategies(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    provider: Optional[str] = None,
) -> tuple[List[StrategyHistory], int]:
    """Get strategies with pagination and filtering."""
    
    query = db.query(StrategyHistory)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            StrategyHistory.title.ilike(search_term) |
            StrategyHistory.jira_ids.ilike(search_term) |
            StrategyHistory.content.ilike(search_term)
        )
    
    if provider:
        query = query.filter(StrategyHistory.provider == provider)
    
    total = query.count()
    strategies = query.order_by(StrategyHistory.created_at.desc()).offset(skip).limit(limit).all()
    
    return strategies, total


def delete_strategy(db: Session, strategy_id: int) -> bool:
    """Delete a strategy by ID."""
    strategy = get_strategy(db, strategy_id)
    if strategy:
        db.delete(strategy)
        db.commit()
        return True
    return False
