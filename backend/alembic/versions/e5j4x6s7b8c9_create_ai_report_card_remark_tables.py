"""create ai report card remark tables

Revision ID: e5j4x6s7b8c9
Revises: d4i3w5r6a7b8
Create Date: 2026-09-02 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e5j4x6s7b8c9'
down_revision: Union[str, None] = 'd4i3w5r6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_report_card_remarks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('report_card_id', sa.UUID(), nullable=False),
        sa.Column('student_id', sa.UUID(), nullable=False),
        sa.Column('created_by_user_id', sa.UUID(), nullable=True),
        sa.Column('tone', sa.String(length=30), nullable=False, server_default='BALANCED'),
        sa.Column('detail_level', sa.String(length=30), nullable=False, server_default='DETAILED'),
        sa.Column('teacher_remarks_draft', sa.Text(), nullable=False),
        sa.Column('principal_remarks_draft', sa.Text(), nullable=False),
        sa.Column('action_items', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('strength_subjects', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('focus_subjects', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('token_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='DRAFT'),
        sa.Column('assessed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['report_card_id'], ['report_cards.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ai_remark_school_card', 'ai_report_card_remarks', ['school_id', 'report_card_id'])
    op.create_index('idx_ai_remark_school_student', 'ai_report_card_remarks', ['school_id', 'student_id'])


def downgrade() -> None:
    op.drop_index('idx_ai_remark_school_student', table_name='ai_report_card_remarks')
    op.drop_index('idx_ai_remark_school_card', table_name='ai_report_card_remarks')
    op.drop_table('ai_report_card_remarks')
