"""Rule Management & Persistence API — owned by Contributor B."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.rules.service import RuleService
from app.schemas.rule import RuleActiveUpdate, RuleCreate, RuleOut, RuleUpdate

router = APIRouter(prefix="/api/rules", tags=["Rules"])


def get_rule_service(db: Session = Depends(get_db)) -> RuleService:
    return RuleService(db)


@router.get("/", response_model=list[RuleOut])
def list_rules(
    category: str | None = None,
    service: RuleService = Depends(get_rule_service),
) -> list[RuleOut]:
    return service.list(category=category)


@router.get("/{rule_id}", response_model=RuleOut)
def get_rule(rule_id: int, service: RuleService = Depends(get_rule_service)) -> RuleOut:
    return service.get(rule_id)


@router.post("/", response_model=RuleOut, status_code=status.HTTP_201_CREATED)
def create_rule(payload: RuleCreate, service: RuleService = Depends(get_rule_service)) -> RuleOut:
    return service.create(payload)


@router.put("/{rule_id}", response_model=RuleOut)
def update_rule(
    rule_id: int,
    payload: RuleUpdate,
    service: RuleService = Depends(get_rule_service),
) -> RuleOut:
    return service.update(rule_id, payload)


@router.patch("/{rule_id}/active", response_model=RuleOut)
def set_rule_active(
    rule_id: int,
    payload: RuleActiveUpdate,
    service: RuleService = Depends(get_rule_service),
) -> RuleOut:
    return service.set_active(rule_id, payload.active)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(rule_id: int, service: RuleService = Depends(get_rule_service)) -> Response:
    service.delete(rule_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
