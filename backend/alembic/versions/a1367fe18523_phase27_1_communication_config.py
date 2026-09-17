"""phase27_1_communication_config

Revision ID: a1367fe18523
Revises: 721c276bdd9d
Create Date: 2026-09-07 22:07:42.153688

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1367fe18523'
down_revision: Union[str, Sequence[str], None] = '721c276bdd9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('school_communication_configs',
    sa.Column('school_id', sa.UUID(), nullable=False),
    sa.Column('sms_provider', sa.Enum('NONE', 'FAST2SMS', 'TWILIO', 'MOCK', name='smsprovidertype'), nullable=False),
    sa.Column('whatsapp_provider', sa.Enum('NONE', 'META_WHATSAPP_CLOUD', 'TWILIO_WHATSAPP', 'MOCK', name='whatsappprovidertype'), nullable=False),
    sa.Column('sms_enabled', sa.Boolean(), nullable=False),
    sa.Column('whatsapp_enabled', sa.Boolean(), nullable=False),
    sa.Column('sms_api_key_encrypted', sa.Text(), nullable=True),
    sa.Column('sms_sender_id', sa.String(length=50), nullable=True),
    sa.Column('sms_entity_id', sa.String(length=100), nullable=True),
    sa.Column('whatsapp_access_token_encrypted', sa.Text(), nullable=True),
    sa.Column('whatsapp_phone_number_id', sa.String(length=100), nullable=True),
    sa.Column('whatsapp_business_account_id', sa.String(length=100), nullable=True),
    sa.Column('sms_monthly_quota', sa.Integer(), nullable=False),
    sa.Column('sms_sent_this_month', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('school_id', name='uq_school_comm_config_school')
    )
    with op.batch_alter_table('school_communication_configs', schema=None) as batch_op:
        batch_op.create_index('ix_school_comm_config_school', ['school_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_school_communication_configs_school_id'), ['school_id'], unique=True)

    with op.batch_alter_table('notification_templates', schema=None) as batch_op:
        batch_op.add_column(sa.Column('dlt_entity_id', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('dlt_template_id', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('whatsapp_template_name', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('whatsapp_language_code', sa.String(length=20), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('notification_templates', schema=None) as batch_op:
        batch_op.drop_column('whatsapp_language_code')
        batch_op.drop_column('whatsapp_template_name')
        batch_op.drop_column('dlt_template_id')
        batch_op.drop_column('dlt_entity_id')

    with op.batch_alter_table('school_communication_configs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_school_communication_configs_school_id'))
        batch_op.drop_index('ix_school_comm_config_school')

    op.drop_table('school_communication_configs')
    # ### end Alembic commands ###
