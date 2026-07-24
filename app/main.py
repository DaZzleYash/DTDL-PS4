"""FastAPI application entry point — owned by Contributor E."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging
from app.exceptions import InvalidRuleError, RuleNotFoundError
from app.schemas.errors import ErrorResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting Finance Decision Engine (env=%s)", settings.app_env)
    yield
    logger.info("Shutting down Finance Decision Engine")


app = FastAPI(
    title="Finance Decision Engine",
    description=(
        "Configurable Decision Automation Platform — evaluates loan/credit "
        "applications against configurable rules and returns explainable decisions."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


def _error_response(status_code: int, error: str, message: str, path: str) -> JSONResponse:
    body = ErrorResponse(
        status=status_code,
        error=error,
        message=message,
        path=path,
    )
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))


@app.exception_handler(RuleNotFoundError)
async def rule_not_found_handler(request: Request, exc: RuleNotFoundError) -> JSONResponse:
    return _error_response(
        status.HTTP_404_NOT_FOUND,
        "Not Found",
        str(exc),
        request.url.path,
    )


@app.exception_handler(InvalidRuleError)
async def invalid_rule_handler(request: Request, exc: InvalidRuleError) -> JSONResponse:
    return _error_response(
        status.HTTP_400_BAD_REQUEST,
        "Bad Request",
        exc.message,
        request.url.path,
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_response(
        status.HTTP_400_BAD_REQUEST,
        "Bad Request",
        str(exc.errors()),
        request.url.path,
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s", request.url.path)
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "Internal Server Error",
        "An unexpected error occurred.",
        request.url.path,
    )


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint for load balancers and Docker."""
    return {
        "status": "healthy",
        "environment": settings.app_env,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# Router wiring — uncomment as each module lands (Phase 1 / Phase 2)
# ---------------------------------------------------------------------------
# from app.rules.router import router as rules_router
# from app.decisions.router import router as decisions_router
#
# app.include_router(rules_router)
# app.include_router(decisions_router)
