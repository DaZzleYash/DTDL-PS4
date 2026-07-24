"""Exception handler tests — Contributor E."""

import asyncio
from unittest.mock import MagicMock

from app.exceptions import InvalidRuleError, RuleNotFoundError
from app.main import invalid_rule_handler, rule_not_found_handler


def test_rule_not_found_returns_404() -> None:
    request = MagicMock()
    request.url.path = "/api/rules/999"
    response = asyncio.run(rule_not_found_handler(request, RuleNotFoundError(999)))
    assert response.status_code == 404
    body = response.body.decode()
    assert "404" in body
    assert "Not Found" in body
    assert "999" in body


def test_invalid_rule_returns_400() -> None:
    request = MagicMock()
    request.url.path = "/api/rules"
    response = asyncio.run(
        invalid_rule_handler(request, InvalidRuleError("Unknown condition type: FOO"))
    )
    assert response.status_code == 400
    body = response.body.decode()
    assert "400" in body
    assert "Bad Request" in body
    assert "FOO" in body
