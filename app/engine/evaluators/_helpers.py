"""Shared helpers for leaf evaluators — owned by Contributor A."""

from app.exceptions import InvalidRuleError


def require_keys(condition: dict, *keys: str, type_label: str) -> None:
    missing = [key for key in keys if key not in condition]
    if missing:
        raise InvalidRuleError(
            f"{type_label} condition missing required field(s): {', '.join(missing)}"
        )


def require_operator(operator: str, allowed: set[str], type_label: str) -> None:
    if operator not in allowed:
        allowed_list = ", ".join(sorted(allowed))
        raise InvalidRuleError(
            f"{type_label} condition has unsupported operator '{operator}'. "
            f"Supported: {allowed_list}"
        )


def missing_field_explanation(field: str) -> str:
    return f"Field '{field}' is missing or null — condition not matched"
