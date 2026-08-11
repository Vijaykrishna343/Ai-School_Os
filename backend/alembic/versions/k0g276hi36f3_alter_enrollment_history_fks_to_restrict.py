"""alter_enrollment_history_fks_to_restrict

Revision ID: k0g276hi36f3
Revises: j9f165gh25e2
Create Date: 2026-08-10 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'k0g276hi36f3'
down_revision: Union[str, Sequence[str], None] = 'j9f165gh25e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: alter school_class_id and section_id FKs to RESTRICT."""
    op.drop_constraint(
        'student_enrollment_histories_school_class_id_fkey',
        'student_enrollment_histories',
        type_='foreignkey',
    )
    op.drop_constraint(
        'student_enrollment_histories_section_id_fkey',
        'student_enrollment_histories',
        type_='foreignkey',
    )
    op.create_foreign_key(
        'student_enrollment_histories_school_class_id_fkey',
        'student_enrollment_histories',
        'school_classes',
        ['school_class_id'],
        ['id'],
        ondelete='RESTRICT',
    )
    op.create_foreign_key(
        'student_enrollment_histories_section_id_fkey',
        'student_enrollment_histories',
        'sections',
        ['section_id'],
        ['id'],
        ondelete='RESTRICT',
    )


def downgrade() -> None:
    """Downgrade schema: revert school_class_id and section_id FKs to CASCADE."""
    op.drop_constraint(
        'student_enrollment_histories_school_class_id_fkey',
        'student_enrollment_histories',
        type_='foreignkey',
    )
    op.drop_constraint(
        'student_enrollment_histories_section_id_fkey',
        'student_enrollment_histories',
        type_='foreignkey',
    )
    op.create_foreign_key(
        'student_enrollment_histories_school_class_id_fkey',
        'student_enrollment_histories',
        'school_classes',
        ['school_class_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        'student_enrollment_histories_section_id_fkey',
        'student_enrollment_histories',
        'sections',
        ['section_id'],
        ['id'],
        ondelete='CASCADE',
    )
