"""
Employee ID Generator Utility.

This module provides functionality for generating unique
teacher employee IDs.

Format:
    EMP000001
    EMP000002
    EMP000003
    ...

The next employee ID is generated based on the latest
existing teacher employee ID.
"""

from app.models.teacher import Teacher


class EmployeeIdGenerator:
    """
    Utility class for generating teacher employee IDs.
    """

    PREFIX = "EMP"
    NUMBER_LENGTH = 6

    @classmethod
    def generate(
        cls,
        last_teacher: Teacher | None,
    ) -> str:
        """
        Generate the next employee ID.

        Args:
            last_teacher:
                Latest teacher ordered by employee ID.

        Returns:
            New employee ID.

        Examples:
            None -> EMP000001

            EMP000001 -> EMP000002

            EMP000999 -> EMP001000
        """

        if last_teacher is None:
            return f"{cls.PREFIX}{1:0{cls.NUMBER_LENGTH}d}"

        employee_id = last_teacher.employee_id

        if (
            not employee_id
            or not employee_id.startswith(cls.PREFIX)
        ):
            return f"{cls.PREFIX}{1:0{cls.NUMBER_LENGTH}d}"

        numeric_part = employee_id.replace(
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