"""
Admission Number Generator Utility.

This module provides functionality for generating unique
student admission numbers.

Format:
    ADM000001
    ADM000002
    ADM000003
    ...

The next admission number is generated based on the latest
existing student admission number.
"""

from app.common.utils.sequence_generator import SequenceCodeGenerator
from app.models.student import Student


class AdmissionNumberGenerator:
    """
    Utility class for generating student admission numbers.
    """

    PREFIX = "ADM"
    NUMBER_LENGTH = 6

    @classmethod
    def generate(
        cls,
        last_student: Student | None,
    ) -> str:
        """
        Generate the next admission number.

        Args:
            last_student:
                Latest student ordered by admission number.

        Returns:
            New admission number.

        Examples:
            None -> ADM000001
            ADM000001 -> ADM000002
            ADM000999 -> ADM001000
        """
        last_code = last_student.admission_number if last_student else None
        return SequenceCodeGenerator.generate_next_code(
            current_code=last_code,
            prefix=cls.PREFIX,
            number_length=cls.NUMBER_LENGTH,
        )
