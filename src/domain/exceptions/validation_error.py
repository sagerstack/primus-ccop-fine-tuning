"""
Domain Validation Error

Custom exception for domain-level validation failures.
Pure domain exception with no external dependencies.
"""


class ValidationError(Exception):
    """
    Exception raised when domain validation rules are violated.

    This is a domain-specific exception that indicates business rule
    violations during entity creation or modification.

    Examples:
        - Invalid test_id format
        - Missing required fields
        - Invalid enum values
        - Constraint violations
    """

    def __init__(self, message: str, field: str | None = None) -> None:
        """
        Initialize validation error.

        Args:
            message: Human-readable error message
            field: Optional field name that failed validation
        """
        self.field = field
        if field:
            super().__init__(f"Validation error in field '{field}': {message}")
        else:
            super().__init__(f"Validation error: {message}")

    def __str__(self) -> str:
        return self.args[0]

    def __repr__(self) -> str:
        if self.field:
            return f"ValidationError(field='{self.field}', message='{self.args[0]}')"
        return f"ValidationError(message='{self.args[0]}')"
