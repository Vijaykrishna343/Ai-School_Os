"""
Sequence Code Generator Utility.

Provides reusable logic for generating prefixed sequential codes
(e.g., ADM000001, EMP000001, 001).
"""


class SequenceCodeGenerator:
    """
    Utility class to generate sequential codes with a prefix and zero-padding.
    """

    @staticmethod
    def generate_next_code(
        current_code: str | None,
        prefix: str = "",
        number_length: int = 6,
    ) -> str:
        """
        Generate the next code based on the previous code.

        Args:
            current_code: The last generated code string, if available.
            prefix: Code prefix string (e.g. 'ADM', 'EMP', or '').
            number_length: Digits for zero-padding.

        Returns:
            The newly formatted sequential code string.
        """
        default_val = f"{prefix}{1:0{number_length}d}"

        if not current_code:
            return default_val

        if prefix and not current_code.startswith(prefix):
            return default_val

        numeric_part = (
            current_code[len(prefix) :]
            if prefix
            else current_code
        )

        try:
            next_number = int(numeric_part) + 1
        except ValueError:
            return default_val

        return f"{prefix}{next_number:0{number_length}d}"
