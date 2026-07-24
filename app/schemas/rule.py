"""Shared rule schemas — owner: Contributor B (agreed in Phase 0)."""

from datetime import datetime

from pydantic import BaseModel, Field


class RuleCreate(BaseModel):
    name: str
    description: str | None = None
    category: str | None = None  # e.g. "ELIGIBILITY", "RISK", "FRAUD"
    priority: int = 0
    active: bool = True
    condition: dict  # JSON condition tree — see spec §5.1
    decision_outcome: str  # "APPROVE" | "REJECT" | "MANUAL_REVIEW" | custom
    decision_metadata: dict | None = None  # e.g. {"riskTier": "B"}


class RuleUpdate(RuleCreate):
    pass


class RuleActiveUpdate(BaseModel):
    active: bool


class RuleOut(RuleCreate):
    id: int
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
