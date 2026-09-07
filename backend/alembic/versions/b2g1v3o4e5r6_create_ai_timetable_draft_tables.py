"""create ai timetable draft tables

Revision ID: b2g1v3o4e5r6
Revises: a1f0u2n3d4a5
Create Date: 2026-08-26 21:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b2g1v3o4e5r6'
down_revision = 'a1f0u2n3d4a5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. ai_timetable_drafts
    op.create_table(
        'ai_timetable_drafts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('academic_year_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, server_default='AI Timetable Draft'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='DRAFT'),
        sa.Column('solver_status', sa.String(length=30), nullable=False, server_default='UNKNOWN'),
        sa.Column('objective_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('solver_duration_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('constraint_summary', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('validation_report', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('approved_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('published_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['academic_year_id'], ['academic_years.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approved_by_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_id'], ['identity_users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['published_by_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_timetable_drafts_academic_year_id'), 'ai_timetable_drafts', ['academic_year_id'], unique=False)
    op.create_index(op.f('ix_ai_timetable_drafts_school_id'), 'ai_timetable_drafts', ['school_id'], unique=False)
    op.create_index(op.f('ix_ai_timetable_drafts_status'), 'ai_timetable_drafts', ['status'], unique=False)

    # 2. ai_timetable_draft_entries
    op.create_table(
        'ai_timetable_draft_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('draft_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('school_class_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('section_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('teacher_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('classroom_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('period_slot_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('day_of_week', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['classroom_id'], ['classrooms.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['draft_id'], ['ai_timetable_drafts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['period_slot_id'], ['period_slots.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_class_id'], ['school_classes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['section_id'], ['sections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_timetable_draft_entries_draft_id'), 'ai_timetable_draft_entries', ['draft_id'], unique=False)
    op.create_index(op.f('ix_ai_timetable_draft_entries_section_id'), 'ai_timetable_draft_entries', ['section_id'], unique=False)
    op.create_index(op.f('ix_ai_timetable_draft_entries_teacher_id'), 'ai_timetable_draft_entries', ['teacher_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ai_timetable_draft_entries_teacher_id'), table_name='ai_timetable_draft_entries')
    op.drop_index(op.f('ix_ai_timetable_draft_entries_section_id'), table_name='ai_timetable_draft_entries')
    op.drop_index(op.f('ix_ai_timetable_draft_entries_draft_id'), table_name='ai_timetable_draft_entries')
    op.drop_table('ai_timetable_draft_entries')
    op.drop_index(op.f('ix_ai_timetable_drafts_status'), table_name='ai_timetable_drafts')
    op.drop_index(op.f('ix_ai_timetable_drafts_school_id'), table_name='ai_timetable_drafts')
    op.drop_index(op.f('ix_ai_timetable_drafts_academic_year_id'), table_name='ai_timetable_drafts')
    op.drop_table('ai_timetable_drafts')
