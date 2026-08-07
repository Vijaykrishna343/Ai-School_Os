"""
Roll Number Generator Utility.

This module provides functionality for generating
student roll numbers within a specific:

- Academic Year
- Class
- Section

Format:
    001
    002
    003
    ...

Roll numbers restart for every Academic Year + Class + Section.
"""

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
                Latest student in the same
                Academic Year + Class + Section.

        Returns:
            Next roll number.

        Examples:
            None -> 001

            001 -> 002

            099 -> 100
        """

        if last_student is None:
            return f"{1:0{cls.NUMBER_LENGTH}d}"

        roll_number = last_student.roll_number

        if not roll_number:
            return f"{1:0{cls.NUMBER_LENGTH}d}"

        try:
            next_number = int(roll_number) + 1

        except ValueError:
            next_number = 1

        return f"{next_number:0{cls.NUMBER_LENGTH}d}"