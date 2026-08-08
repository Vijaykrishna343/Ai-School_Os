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

from app.common.utils.sequence_generator import SequenceCodeGenerator
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
        last_code = last_teacher.employee_id if last_teacher else None
        return SequenceCodeGenerator.generate_next_code(
            current_code=last_code,
            prefix=cls.PREFIX,
            number_length=cls.NUMBER_LENGTH,
        )
