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

        if last_student is None:
            return f"{cls.PREFIX}{1:0{cls.NUMBER_LENGTH}d}"

        admission_number = last_student.admission_number

        if (
            not admission_number
            or not admission_number.startswith(cls.PREFIX)
        ):
            return f"{cls.PREFIX}{1:0{cls.NUMBER_LENGTH}d}"

        numeric_part = admission_number.replace(
            cls.PREFIX,
            "",
        )

        try:
            next_number = int(numeric_part) + 1

        except ValueError:
            next_number = 1

        return (
            f"{cls.PREFIX}"
            f"{next_number:0{cls.NUMBER_LENGTH}d}"
        )