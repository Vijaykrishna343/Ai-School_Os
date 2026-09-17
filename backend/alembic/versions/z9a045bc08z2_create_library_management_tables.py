"""create_library_management_tables

Revision ID: z9a045bc08z2
Revises: z9a045bc07z1
Create Date: 2026-09-12 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'z9a045bc08z2'
down_revision: Union[str, Sequence[str], None] = 'z9a045bc07z1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. libraries
    op.create_table(
        'libraries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('libraries', schema=None) as batch_op:
        batch_op.create_index('ix_libraries_school_id', ['school_id'], unique=False)
        batch_op.create_index(
            'uq_library_school_code',
            ['school_id', 'code'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false'),
            sqlite_where=sa.text('is_deleted = 0')
        )
        batch_op.create_index(
            'uq_library_school_name',
            ['school_id', 'name'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false'),
            sqlite_where=sa.text('is_deleted = 0')
        )

    # 2. library_categories
    op.create_table(
        'library_categories',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('library_categories', schema=None) as batch_op:
        batch_op.create_index('ix_library_categories_school_id', ['school_id'], unique=False)
        batch_op.create_index(
            'uq_library_category_school_name',
            ['school_id', 'name'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false'),
            sqlite_where=sa.text('is_deleted = 0')
        )
        batch_op.create_index(
            'uq_library_category_school_code',
            ['school_id', 'code'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false AND code IS NOT NULL'),
            sqlite_where=sa.text('is_deleted = 0 AND code IS NOT NULL')
        )

    # 3. library_books
    op.create_table(
        'library_books',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('library_id', sa.UUID(), nullable=True),
        sa.Column('category_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('subtitle', sa.String(length=255), nullable=True),
        sa.Column('author', sa.String(length=255), nullable=False),
        sa.Column('publisher', sa.String(length=255), nullable=True),
        sa.Column('publication_year', sa.Integer(), nullable=True),
        sa.Column('isbn', sa.String(length=50), nullable=True),
        sa.Column('edition', sa.String(length=50), nullable=True),
        sa.Column('language', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('total_pages', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['library_id'], ['libraries.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['category_id'], ['library_categories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('library_books', schema=None) as batch_op:
        batch_op.create_index('ix_library_books_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_library_books_title', ['title'], unique=False)
        batch_op.create_index('ix_library_books_author', ['author'], unique=False)
        batch_op.create_index('ix_library_books_isbn', ['isbn'], unique=False)
        batch_op.create_index('ix_library_books_category_id', ['category_id'], unique=False)
        batch_op.create_index('ix_library_books_library_id', ['library_id'], unique=False)
        batch_op.create_index('ix_library_books_school_title', ['school_id', 'title'], unique=False)

    # 4. library_book_copies
    op.create_table(
        'library_book_copies',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('book_id', sa.UUID(), nullable=False),
        sa.Column('accession_number', sa.String(length=50), nullable=False),
        sa.Column('barcode', sa.String(length=100), nullable=True),
        sa.Column('rfid_tag', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('AVAILABLE', 'ISSUED', 'RESERVED', 'MAINTENANCE', 'LOST', 'DAMAGED', 'WRITTEN_OFF', name='bookcopystatus', native_enum=False), nullable=False),
        sa.Column('condition', sa.Enum('NEW', 'GOOD', 'FAIR', 'POOR', 'DAMAGED', name='bookcondition', native_enum=False), nullable=False),
        sa.Column('shelf_location', sa.String(length=100), nullable=True),
        sa.Column('acquisition_date', sa.Date(), nullable=True),
        sa.Column('acquisition_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('acquisition_price IS NULL OR acquisition_price >= 0', name='ck_library_book_copy_price_non_neg'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['book_id'], ['library_books.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('library_book_copies', schema=None) as batch_op:
        batch_op.create_index('ix_library_book_copies_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_library_book_copies_book_id', ['book_id'], unique=False)
        batch_op.create_index('ix_library_book_copies_status', ['status'], unique=False)
        batch_op.create_index('ix_library_book_copies_condition', ['condition'], unique=False)
        batch_op.create_index('ix_library_book_copies_shelf', ['shelf_location'], unique=False)
        batch_op.create_index(
            'uq_library_copy_school_accession',
            ['school_id', 'accession_number'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false'),
            sqlite_where=sa.text('is_deleted = 0')
        )
        batch_op.create_index(
            'uq_library_copy_school_barcode',
            ['school_id', 'barcode'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false AND barcode IS NOT NULL'),
            sqlite_where=sa.text('is_deleted = 0 AND barcode IS NOT NULL')
        )

    # 5. library_members
    op.create_table(
        'library_members',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('member_type', sa.Enum('STUDENT', 'TEACHER', 'STAFF', name='librarymembertype', native_enum=False), nullable=False),
        sa.Column('student_id', sa.UUID(), nullable=True),
        sa.Column('teacher_id', sa.UUID(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('card_number', sa.String(length=50), nullable=False),
        sa.Column('issue_date', sa.Date(), nullable=False),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('max_books_allowed', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'SUSPENDED', 'EXPIRED', 'CANCELLED', name='librarymemberstatus', native_enum=False), nullable=False),
        sa.Column('remarks', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('max_books_allowed > 0', name='ck_library_member_max_books_pos'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('library_members', schema=None) as batch_op:
        batch_op.create_index('ix_library_members_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_library_members_student_id', ['student_id'], unique=False)
        batch_op.create_index('ix_library_members_teacher_id', ['teacher_id'], unique=False)
        batch_op.create_index('ix_library_members_user_id', ['user_id'], unique=False)
        batch_op.create_index('ix_library_members_status', ['status'], unique=False)
        batch_op.create_index('ix_library_members_member_type', ['member_type'], unique=False)
        batch_op.create_index(
            'uq_library_member_school_card',
            ['school_id', 'card_number'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false'),
            sqlite_where=sa.text('is_deleted = 0')
        )
        batch_op.create_index(
            'uq_library_member_school_student',
            ['school_id', 'student_id'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false AND student_id IS NOT NULL'),
            sqlite_where=sa.text('is_deleted = 0 AND student_id IS NOT NULL')
        )
        batch_op.create_index(
            'uq_library_member_school_teacher',
            ['school_id', 'teacher_id'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false AND teacher_id IS NOT NULL'),
            sqlite_where=sa.text('is_deleted = 0 AND teacher_id IS NOT NULL')
        )
        batch_op.create_index(
            'uq_library_member_school_user',
            ['school_id', 'user_id'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false AND user_id IS NOT NULL'),
            sqlite_where=sa.text('is_deleted = 0 AND user_id IS NOT NULL')
        )

    # 6. library_book_loans
    op.create_table(
        'library_book_loans',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('member_id', sa.UUID(), nullable=False),
        sa.Column('book_copy_id', sa.UUID(), nullable=False),
        sa.Column('issue_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('return_date', sa.Date(), nullable=True),
        sa.Column('renewal_count', sa.Integer(), nullable=False),
        sa.Column('max_renewals', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('ISSUED', 'RETURNED', 'OVERDUE', 'LOST', 'DAMAGED', name='bookloanstatus', native_enum=False), nullable=False),
        sa.Column('issued_by_user_id', sa.UUID(), nullable=True),
        sa.Column('received_by_user_id', sa.UUID(), nullable=True),
        sa.Column('remarks', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('due_date >= issue_date', name='ck_library_loan_due_after_issue'),
        sa.CheckConstraint('return_date IS NULL OR return_date >= issue_date', name='ck_library_loan_return_after_issue'),
        sa.CheckConstraint('renewal_count >= 0', name='ck_library_loan_renewal_count_non_neg'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['member_id'], ['library_members.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['book_copy_id'], ['library_book_copies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['issued_by_user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['received_by_user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('library_book_loans', schema=None) as batch_op:
        batch_op.create_index('ix_library_book_loans_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_library_book_loans_member_id', ['member_id'], unique=False)
        batch_op.create_index('ix_library_book_loans_copy_id', ['book_copy_id'], unique=False)
        batch_op.create_index('ix_library_book_loans_status', ['status'], unique=False)
        batch_op.create_index('ix_library_book_loans_due_date', ['due_date'], unique=False)
        batch_op.create_index('ix_library_book_loans_issue_date', ['issue_date'], unique=False)
        batch_op.create_index(
            'uq_active_loan_per_book_copy',
            ['school_id', 'book_copy_id'],
            unique=True,
            postgresql_where=sa.text("is_deleted = false AND status IN ('ISSUED', 'OVERDUE')"),
            sqlite_where=sa.text("is_deleted = 0 AND status IN ('ISSUED', 'OVERDUE')")
        )

    # 7. library_book_reservations
    op.create_table(
        'library_book_reservations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('member_id', sa.UUID(), nullable=False),
        sa.Column('book_id', sa.UUID(), nullable=False),
        sa.Column('reservation_date', sa.Date(), nullable=False),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'FULFILLED', 'CANCELLED', 'EXPIRED', name='bookreservationstatus', native_enum=False), nullable=False),
        sa.Column('remarks', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['member_id'], ['library_members.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['book_id'], ['library_books.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('library_book_reservations', schema=None) as batch_op:
        batch_op.create_index('ix_library_book_reservations_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_library_book_reservations_member_id', ['member_id'], unique=False)
        batch_op.create_index('ix_library_book_reservations_book_id', ['book_id'], unique=False)
        batch_op.create_index('ix_library_book_reservations_status', ['status'], unique=False)
        batch_op.create_index('ix_library_book_reservations_date', ['reservation_date'], unique=False)
        batch_op.create_index(
            'uq_pending_member_book_reservation',
            ['school_id', 'member_id', 'book_id'],
            unique=True,
            postgresql_where=sa.text("is_deleted = false AND status = 'PENDING'"),
            sqlite_where=sa.text("is_deleted = 0 AND status = 'PENDING'")
        )

    # 8. library_fines
    op.create_table(
        'library_fines',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('loan_id', sa.UUID(), nullable=False),
        sa.Column('member_id', sa.UUID(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('fine_reason', sa.Enum('OVERDUE', 'DAMAGED_BOOK', 'LOST_BOOK', 'OTHER', name='libraryfinereason', native_enum=False), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PAID', 'WAIVED', name='libraryfinestatus', native_enum=False), nullable=False),
        sa.Column('paid_date', sa.Date(), nullable=True),
        sa.Column('waived_reason', sa.String(length=255), nullable=True),
        sa.Column('waived_by_user_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('amount >= 0', name='ck_library_fine_amount_non_neg'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['loan_id'], ['library_book_loans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['member_id'], ['library_members.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['waived_by_user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('library_fines', schema=None) as batch_op:
        batch_op.create_index('ix_library_fines_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_library_fines_loan_id', ['loan_id'], unique=False)
        batch_op.create_index('ix_library_fines_member_id', ['member_id'], unique=False)
        batch_op.create_index('ix_library_fines_status', ['status'], unique=False)
        batch_op.create_index('ix_library_fines_reason', ['fine_reason'], unique=False)


def downgrade() -> None:
    op.drop_table('library_fines')
    op.drop_table('library_book_reservations')
    op.drop_table('library_book_loans')
    op.drop_table('library_members')
    op.drop_table('library_book_copies')
    op.drop_table('library_books')
    op.drop_table('library_categories')
    op.drop_table('libraries')
