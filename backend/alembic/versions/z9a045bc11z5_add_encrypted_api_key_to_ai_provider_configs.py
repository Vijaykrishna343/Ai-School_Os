"""add_encrypted_api_key_to_ai_provider_configs

Revision ID: z9a045bc11z5
Revises: z9a045bc10z4
Create Date: 2026-09-14 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'z9a045bc11z5'
down_revision: Union[str, Sequence[str], None] = 'z9a045bc10z4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ai_provider_configs', sa.Column('encrypted_api_key', sa.Text(), nullable=True))
    op.add_column('ai_provider_configs', sa.Column('api_base_url', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('ai_provider_configs', 'api_base_url')
    op.drop_column('ai_provider_configs', 'encrypted_api_key')
