"""add_assessment_and_attempt_types_to_exams

Revision ID: l2i498jk58h5
Revises: l1h387ij47g4
Create Date: 2026-08-11 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'l2i498jk58h5'
down_revision: Union[str, Sequence[str], None] = 'l1h387ij47g4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

assessment_type_values = (
    'FORMATIVE_ASSESSMENT',
    'SUMMATIVE_ASSESSMENT',
    'UNIT_TEST',
    'PERIODIC_TEST',
    'QUARTERLY',
    'HALF_YEARLY',
    'TERM',
    'PRE_FINAL',
    'QUARTER_FINAL',
    'SEMI_FINAL',
    'FINAL',
    'OTHER',
)

attempt_type_values = (
    'REGULAR',
    'RETEST',
    'MAKEUP',
)


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == 'postgresql'

    if is_postgres:
        assessment_enum = postgresql.ENUM(*assessment_type_values, name='assessment_type')
        attempt_enum = postgresql.ENUM(*attempt_type_values, name='attempt_type')
        assessment_enum.create(bind, checkfirst=True)
        attempt_enum.create(bind, checkfirst=True)

        assessment_type_col = sa.Column('assessment_type', sa.Enum(*assessment_type_values, name='assessment_type'), nullable=True)
        attempt_type_col = sa.Column('attempt_type', sa.Enum(*attempt_type_values, name='attempt_type'), nullable=True)
    else:
        assessment_type_col = sa.Column('assessment_type', sa.Enum(*assessment_type_values, name='assessment_type'), nullable=True)
        attempt_type_col = sa.Column('attempt_type', sa.Enum(*attempt_type_values, name='attempt_type'), nullable=True)

    op.add_column('exams', assessment_type_col)
    op.add_column('exams', attempt_type_col)

    op.execute("UPDATE exams SET attempt_type = 'REGULAR', assessment_type = 'OTHER' WHERE CAST(exam_type AS text) = 'REGULAR'")
    op.execute("UPDATE exams SET attempt_type = 'RETEST', assessment_type = 'OTHER' WHERE CAST(exam_type AS text) = 'RETEST'")
    op.execute("UPDATE exams SET attempt_type = 'REGULAR', assessment_type = 'OTHER' WHERE CAST(exam_type AS text) = 'OTHER' OR exam_type IS NULL")

    op.alter_column('exams', 'assessment_type', nullable=False, server_default='OTHER')
    op.alter_column('exams', 'attempt_type', nullable=False, server_default='REGULAR')

    op.drop_index('ix_exams_exam_type', table_name='exams', if_exists=True)
    op.drop_column('exams', 'exam_type')

    if is_postgres:
        op.execute("DROP TYPE IF EXISTS exam_type CASCADE")

    op.create_index('ix_exams_assessment_type', 'exams', ['assessment_type'], unique=False)
    op.create_index('ix_exams_attempt_type', 'exams', ['attempt_type'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == 'postgresql'

    if is_postgres:
        old_enum = postgresql.ENUM('REGULAR', 'RETEST', 'OTHER', name='exam_type')
        old_enum.create(bind, checkfirst=True)
        exam_type_col = sa.Column('exam_type', sa.Enum('REGULAR', 'RETEST', 'OTHER', name='exam_type'), nullable=True)
    else:
        exam_type_col = sa.Column('exam_type', sa.Enum('REGULAR', 'RETEST', 'OTHER', name='exam_type'), nullable=True)

    op.add_column('exams', exam_type_col)

    op.execute("UPDATE exams SET exam_type = 'RETEST' WHERE CAST(attempt_type AS text) = 'RETEST'")
    op.execute("UPDATE exams SET exam_type = 'REGULAR' WHERE CAST(attempt_type AS text) = 'REGULAR' OR CAST(attempt_type AS text) = 'MAKEUP' OR attempt_type IS NULL")

    op.alter_column('exams', 'exam_type', nullable=False, server_default='REGULAR')

    op.drop_index('ix_exams_attempt_type', table_name='exams', if_exists=True)
    op.drop_index('ix_exams_assessment_type', table_name='exams', if_exists=True)
    op.drop_column('exams', 'attempt_type')
    op.drop_column('exams', 'assessment_type')

    if is_postgres:
        op.execute("DROP TYPE IF EXISTS assessment_type CASCADE")
        op.execute("DROP TYPE IF EXISTS attempt_type CASCADE")

    op.create_index('ix_exams_exam_type', 'exams', ['exam_type'], unique=False)
