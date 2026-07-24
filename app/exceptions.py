"""Domain exceptions — owned by Contributor E."""


class RuleNotFoundError(Exception):
    """Raised when a rule with the given ID does not exist."""

    def __init__(self, rule_id: int) -> None:
        self.rule_id = rule_id
        super().__init__(f"Rule with id {rule_id} not found")


class InvalidRuleError(Exception):
    """Raised when a rule's condition tree is malformed or unsupported."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
