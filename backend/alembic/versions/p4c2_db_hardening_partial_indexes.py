"""p4c2_db_hardening_partial_indexes

Revision ID: p4c2_db_hardening
Revises: o3s387tu47q4
Create Date: 2026-08-13 16:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'p4c2_db_hardening'
down_revision: Union[str, Sequence[str], None] = 'o3s387tu47q4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop old strict unique constraints
    op.drop_constraint('uq_academic_year_school_name', 'academic_years', type_='unique')
    op.drop_constraint('uq_school_classes_school_id_name', 'school_classes', type_='unique')
    op.drop_constraint('uq_sections_school_class_id_name', 'sections', type_='unique')
    op.drop_constraint('uq_student_roll_number', 'students', type_='unique')
    op.drop_constraint('uq_student_admission_number', 'students', type_='unique')
    op.drop_constraint('uq_student_enrollment_history_year', 'student_enrollment_histories', type_='unique')
    op.drop_constraint('uq_tc_school_number', 'transfer_certificates', type_='unique')

    # 2. Create partial unique indexes (WHERE is_deleted = false / is_deleted = 0)
    op.create_index(
        'uq_academic_years_school_name_active',
        'academic_years',
        ['school_id', 'name'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false'),
        sqlite_where=sa.text('is_deleted = 0'),
    )
    op.create_index(
        'uq_school_classes_school_name_active',
        'school_classes',
        ['school_id', 'name'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false'),
        sqlite_where=sa.text('is_deleted = 0'),
    )
    op.create_index(
        'uq_sections_class_name_active',
        'sections',
        ['school_class_id', 'name'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false'),
        sqlite_where=sa.text('is_deleted = 0'),
    )
    op.create_index(
        'uq_students_roll_number_active',
        'students',
        ['academic_year_id', 'school_class_id', 'roll_number'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false'),
        sqlite_where=sa.text('is_deleted = 0'),
    )
    op.create_index(
        'uq_students_admission_number_active',
        'students',
        ['admission_number'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false'),
        sqlite_where=sa.text('is_deleted = 0'),
    )
    op.create_index(
        'uq_enrollment_history_year_active',
        'student_enrollment_histories',
        ['school_id', 'student_id', 'academic_year_id'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false'),
        sqlite_where=sa.text('is_deleted = 0'),
    )
    op.create_index(
        'uq_tc_school_number_active',
        'transfer_certificates',
        ['school_id', 'tc_number'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false'),
        sqlite_where=sa.text('is_deleted = 0'),
    )

    # 3. Create performance composite indexes
    op.create_index(
        'ix_attendances_school_date',
        'attendances',
        ['school_id', 'attendance_date'],
    )
    op.create_index(
        'ix_fee_assignments_school_year_student',
        'student_fee_assignments',
        ['school_id', 'academic_year_id', 'student_id'],
    )


def downgrade() -> None:
    # 1. Drop composite performance indexes
    op.drop_index('ix_fee_assignments_school_year_student', table_name='student_fee_assignments')
    op.drop_index('ix_attendances_school_date', table_name='attendances')

    # 2. Drop partial unique indexes
    op.drop_index('uq_tc_school_number_active', table_name='transfer_certificates')
    op.drop_index('uq_enrollment_history_year_active', table_name='student_enrollment_histories')
    op.drop_index('uq_students_admission_number_active', table_name='students')
    op.drop_index('uq_students_roll_number_active', table_name='students')
    op.drop_index('uq_sections_class_name_active', table_name='sections')
    op.drop_index('uq_school_classes_school_name_active', table_name='school_classes')
    op.drop_index('uq_academic_years_school_name_active', table_name='academic_years')

    # 3. Re-create original unique constraints
    op.create_unique_constraint('uq_tc_school_number', 'transfer_certificates', ['school_id', 'tc_number'])
    op.create_unique_constraint('uq_student_enrollment_history_year', 'student_enrollment_histories', ['school_id', 'student_id', 'academic_year_id'])
    op.create_unique_constraint('uq_student_admission_number', 'students', ['admission_number'])
    op.create_unique_constraint('uq_student_roll_number', 'students', ['academic_year_id', 'school_class_id', 'roll_number'])
    op.create_unique_constraint('uq_sections_school_class_id_name', 'sections', ['school_class_id', 'name'])
    op.create_unique_constraint('uq_school_classes_school_id_name', 'school_classes', ['school_id', 'name'])
    op.create_unique_constraint('uq_academic_year_school_name', 'academic_years', ['school_id', 'name'])
