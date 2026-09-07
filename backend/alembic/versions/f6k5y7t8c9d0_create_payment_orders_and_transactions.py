"""create payment orders and transactions

Revision ID: f6k5y7t8c9d0
Revises: e5j4x6s7b8c9
Create Date: 2026-09-06 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6k5y7t8c9d0'
down_revision: Union[str, None] = 'e5j4x6s7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'payment_orders',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('student_fee_assignment_id', sa.UUID(), nullable=False),
        sa.Column('provider', sa.String(length=30), nullable=False),
        sa.Column('gateway_order_id', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='INR'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='CREATED'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('amount > 0', name='ck_payment_orders_amount_positive'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_fee_assignment_id'], ['student_fee_assignments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'gateway_order_id', name='uq_payment_orders_provider_gateway_order_id'),
    )
    op.create_index('ix_payment_orders_school_id', 'payment_orders', ['school_id'])
    op.create_index('ix_payment_orders_assignment_id', 'payment_orders', ['student_fee_assignment_id'])
    op.create_index('ix_payment_orders_status', 'payment_orders', ['status'])
    op.create_index('ix_payment_orders_school_status', 'payment_orders', ['school_id', 'status'])
    op.create_index('ix_payment_orders_school_created', 'payment_orders', ['school_id', 'created_at'])

    op.create_table(
        'payment_transactions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('payment_order_id', sa.UUID(), nullable=False),
        sa.Column('provider', sa.String(length=30), nullable=False),
        sa.Column('gateway_transaction_id', sa.String(length=100), nullable=False),
        sa.Column('gateway_event_id', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='INR'),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('failure_reason', sa.String(length=255), nullable=True),
        sa.Column('event_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('raw_response', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('amount > 0', name='ck_payment_transactions_amount_positive'),
        sa.ForeignKeyConstraint(['payment_order_id'], ['payment_orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_payment_transactions_school_id', 'payment_transactions', ['school_id'])
    op.create_index('ix_payment_transactions_order_id', 'payment_transactions', ['payment_order_id'])
    op.create_index('ix_payment_transactions_status', 'payment_transactions', ['status'])
    op.create_index('ix_payment_transactions_school_created', 'payment_transactions', ['school_id', 'created_at'])
    op.create_index(
        'uq_payment_transaction_provider_txn',
        'payment_transactions',
        ['provider', 'gateway_transaction_id'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false'),
        sqlite_where=sa.text('is_deleted = 0'),
    )


def downgrade() -> None:
    op.drop_index('uq_payment_transaction_provider_txn', table_name='payment_transactions')
    op.drop_index('ix_payment_transactions_school_created', table_name='payment_transactions')
    op.drop_index('ix_payment_transactions_status', table_name='payment_transactions')
    op.drop_index('ix_payment_transactions_order_id', table_name='payment_transactions')
    op.drop_index('ix_payment_transactions_school_id', table_name='payment_transactions')
    op.drop_table('payment_transactions')

    op.drop_index('ix_payment_orders_school_created', table_name='payment_orders')
    op.drop_index('ix_payment_orders_school_status', table_name='payment_orders')
    op.drop_index('ix_payment_orders_status', table_name='payment_orders')
    op.drop_index('ix_payment_orders_assignment_id', table_name='payment_orders')
    op.drop_index('ix_payment_orders_school_id', table_name='payment_orders')
    op.drop_table('payment_orders')
