"""Evaluation context — owned by Contributor A."""


class EvaluationContext:
    """Wraps a request payload and resolves dot-notation field paths."""

    def __init__(self, data: dict) -> None:
        self._data = data

    def resolve_field(self, path: str) -> object | None:
        """Return the value at *path* (e.g. ``applicant.creditScore``), or ``None`` if missing."""
        current: object = self._data
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
        return current
