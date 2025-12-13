"""
Domain Evaluation Error

Custom exception for evaluation-related failures.
Pure domain exception with no external dependencies.
"""


class EvaluationError(Exception):
    """
    Exception raised when evaluation process encounters domain-level errors.

    This is a domain-specific exception that indicates failures during
    the evaluation workflow that are not validation errors.

    Examples:
        - Cannot calculate score with missing data
        - Invalid evaluation criteria
        - Inconsistent evaluation state
        - Business rule violations during scoring
    """

    def __init__(self, message: str, test_case_id: str | None = None) -> None:
        """
        Initialize evaluation error.

        Args:
            message: Human-readable error message
            test_case_id: Optional test case ID where error occurred
        """
        self.test_case_id = test_case_id
        if test_case_id:
            super().__init__(f"Evaluation error for test case '{test_case_id}': {message}")
        else:
            super().__init__(f"Evaluation error: {message}")

    def __str__(self) -> str:
        return self.args[0]

    def __repr__(self) -> str:
        if self.test_case_id:
            return (
                f"EvaluationError(test_case_id='{self.test_case_id}', "
                f"message='{self.args[0]}')"
            )
        return f"EvaluationError(message='{self.args[0]}')"
