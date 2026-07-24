"""Decision Engine & API — owned by Contributor C."""

# ruff: noqa: B008 — FastAPI Depends() in defaults is intentional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.decisions.service import DecisionEngineService
from app.rules.repository import RuleRepository
from app.schemas.decision import DecisionResponse, EvaluateRequest

router = APIRouter(prefix="/api/decisions", tags=["Decisions"])


def get_decision_service(db: Session = Depends(get_db)) -> DecisionEngineService:
    return DecisionEngineService(RuleRepository(db))


@router.post("/evaluate", response_model=DecisionResponse)
def evaluate_decision(
    payload: EvaluateRequest,
    service: DecisionEngineService = Depends(get_decision_service),
) -> DecisionResponse:
    return service.evaluate(payload)


@router.post("/evaluate/bulk", response_model=list[DecisionResponse])
def evaluate_bulk(
    payload: list[EvaluateRequest],
    service: DecisionEngineService = Depends(get_decision_service),
) -> list[DecisionResponse]:
    return service.evaluate_bulk(payload)
