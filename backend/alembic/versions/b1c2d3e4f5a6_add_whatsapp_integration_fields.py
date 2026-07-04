"""add whatsapp integration fields

Revision ID: b1c2d3e4f5a6
Revises: a7b8c9d0e1f2
Create Date: 2026-03-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add WhatsApp API credential columns to widget_settings
    with op.batch_alter_table('widget_settings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('whatsapp_phone_number_id', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('whatsapp_business_account_id', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('whatsapp_access_token', sa.String(), nullable=True))

    # Add channel column to chat_sessions
    with op.batch_alter_table('chat_sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('channel', sa.String(), nullable=True, server_default='widget'))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('chat_sessions', schema=None) as batch_op:
        batch_op.drop_column('channel')

    with op.batch_alter_table('widget_settings', schema=None) as batch_op:
        batch_op.drop_column('whatsapp_access_token')
        batch_op.drop_column('whatsapp_business_account_id')
        batch_op.drop_column('whatsapp_phone_number_id')
