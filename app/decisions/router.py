"""Decision Engine & API — owned by Contributor C."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/decisions", tags=["Decisions"])

# Contributor C: add /evaluate and /evaluate/bulk endpoints here
