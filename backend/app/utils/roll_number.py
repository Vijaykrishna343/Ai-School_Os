"""
Roll Number Generator Utility.

This module provides functionality for generating
student roll numbers within a specific:

- Academic Year
- Class

Format:
    001
    002
    003
    ...

Roll numbers restart for every Academic Year + Class.
"""

from app.common.utils.sequence_generator import SequenceCodeGenerator
from app.models.student import Student


class RollNumberGenerator:
    """
    Utility class for generating student roll numbers.
    """

    NUMBER_LENGTH = 3

    @classmethod
    def generate(
        cls,
        last_student: Student | None,
    ) -> str:
        """
        Generate the next roll number.

        Args:
            last_student:
                Latest student in the same Academic Year + Class.

        Returns:
            Next roll number.

        Examples:
            None -> 001
            001 -> 002
            099 -> 100
        """
        last_code = last_student.roll_number if last_student else None
        return SequenceCodeGenerator.generate_next_code(
            current_code=last_code,
            prefix="",
            number_length=cls.NUMBER_LENGTH,
        )
