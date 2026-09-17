"""create_admissions_management_tables

Revision ID: z9a045bc09z3
Revises: z9a045bc08z2
Create Date: 2026-09-13 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'z9a045bc09z3'
down_revision: Union[str, Sequence[str], None] = 'z9a045bc08z2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. admission_cycles
    op.create_table(
        'admission_cycles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('academic_year_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'ACTIVE', 'CLOSED', 'ARCHIVED', name='admissioncyclestatus', native_enum=False), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('end_date >= start_date', name='ck_admission_cycle_dates_valid'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['academic_year_id'], ['academic_years.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('admission_cycles', schema=None) as batch_op:
        batch_op.create_index('ix_admission_cycles_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_admission_cycles_academic_year_id', ['academic_year_id'], unique=False)
        batch_op.create_index('ix_admission_cycles_status', ['status'], unique=False)
        batch_op.create_index(
            'uq_admission_cycle_school_code',
            ['school_id', 'code'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false'),
            sqlite_where=sa.text('is_deleted = 0')
        )
        batch_op.create_index(
            'uq_admission_cycle_school_name_year',
            ['school_id', 'academic_year_id', 'name'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false'),
            sqlite_where=sa.text('is_deleted = 0')
        )

    # 2. applicants
    op.create_table(
        'applicants',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('admission_cycle_id', sa.UUID(), nullable=True),
        sa.Column('applicant_number', sa.String(length=50), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('middle_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=False),
        sa.Column('gender', sa.String(length=20), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('parent_name', sa.String(length=200), nullable=True),
        sa.Column('parent_phone', sa.String(length=50), nullable=True),
        sa.Column('parent_email', sa.String(length=255), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('PROSPECT', 'APPLIED', 'UNDER_REVIEW', 'SHORTLISTED', 'ACCEPTED', 'REJECTED', 'WITHDRAWN', 'ENROLLED', name='applicantstatus', native_enum=False), nullable=False),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['admission_cycle_id'], ['admission_cycles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('applicants', schema=None) as batch_op:
        batch_op.create_index('ix_applicants_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_applicants_admission_cycle_id', ['admission_cycle_id'], unique=False)
        batch_op.create_index('ix_applicants_status', ['status'], unique=False)
        batch_op.create_index('ix_applicants_names', ['school_id', 'first_name', 'last_name'], unique=False)
        batch_op.create_index(
            'uq_applicant_school_applicant_number',
            ['school_id', 'applicant_number'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false'),
            sqlite_where=sa.text('is_deleted = 0')
        )

    # 3. admission_applications
    op.create_table(
        'admission_applications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('applicant_id', sa.UUID(), nullable=False),
        sa.Column('admission_cycle_id', sa.UUID(), nullable=False),
        sa.Column('academic_year_id', sa.UUID(), nullable=False),
        sa.Column('target_class_id', sa.UUID(), nullable=False),
        sa.Column('target_section_id', sa.UUID(), nullable=True),
        sa.Column('application_number', sa.String(length=50), nullable=False),
        sa.Column('application_date', sa.Date(), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'WAITLISTED', 'ACCEPTED', 'REJECTED', 'WITHDRAWN', 'ENROLLED', name='admissionapplicationstatus', native_enum=False), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decision_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('remarks', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['applicant_id'], ['applicants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['admission_cycle_id'], ['admission_cycles.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['academic_year_id'], ['academic_years.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['target_class_id'], ['school_classes.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['target_section_id'], ['sections.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('admission_applications', schema=None) as batch_op:
        batch_op.create_index('ix_admission_applications_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_admission_applications_applicant_id', ['applicant_id'], unique=False)
        batch_op.create_index('ix_admission_applications_cycle_id', ['admission_cycle_id'], unique=False)
        batch_op.create_index('ix_admission_applications_year_id', ['academic_year_id'], unique=False)
        batch_op.create_index('ix_admission_applications_class_id', ['target_class_id'], unique=False)
        batch_op.create_index('ix_admission_applications_status', ['status'], unique=False)
        batch_op.create_index(
            'uq_admission_app_school_app_number',
            ['school_id', 'application_number'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false'),
            sqlite_where=sa.text('is_deleted = 0')
        )
        batch_op.create_index(
            'uq_admission_app_applicant_cycle_active',
            ['school_id', 'applicant_id', 'admission_cycle_id'],
            unique=True,
            postgresql_where=sa.text("is_deleted = false AND status NOT IN ('REJECTED', 'WITHDRAWN')"),
            sqlite_where=sa.text("is_deleted = 0 AND status NOT IN ('REJECTED', 'WITHDRAWN')")
        )

    # 4. application_status_history
    op.create_table(
        'application_status_history',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('application_id', sa.UUID(), nullable=False),
        sa.Column('old_status', sa.String(length=50), nullable=True),
        sa.Column('new_status', sa.String(length=50), nullable=False),
        sa.Column('changed_by_user_id', sa.UUID(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reason', sa.String(length=500), nullable=True),
        sa.Column('remarks', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['application_id'], ['admission_applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['changed_by_user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('application_status_history', schema=None) as batch_op:
        batch_op.create_index('ix_app_status_hist_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_app_status_hist_application_id', ['application_id'], unique=False)
        batch_op.create_index('ix_app_status_hist_user_id', ['changed_by_user_id'], unique=False)

    # 5. admission_decisions
    op.create_table(
        'admission_decisions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('application_id', sa.UUID(), nullable=False),
        sa.Column('decision_type', sa.Enum('ACCEPTED', 'REJECTED', 'WAITLISTED', 'WITHDRAWN', 'CONDITIONAL_ACCEPT', name='admissiondecisiontype', native_enum=False), nullable=False),
        sa.Column('decided_by_user_id', sa.UUID(), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('comments', sa.String(length=1000), nullable=True),
        sa.Column('conditions', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['application_id'], ['admission_applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['decided_by_user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('admission_decisions', schema=None) as batch_op:
        batch_op.create_index('ix_admission_decisions_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_admission_decisions_application_id', ['application_id'], unique=False)
        batch_op.create_index('ix_admission_decisions_user_id', ['decided_by_user_id'], unique=False)
        batch_op.create_index('ix_admission_decisions_type', ['decision_type'], unique=False)


def downgrade() -> None:
    op.drop_table('admission_decisions')
    op.drop_table('application_status_history')
    op.drop_table('admission_applications')
    op.drop_table('applicants')
    op.drop_table('admission_cycles')
