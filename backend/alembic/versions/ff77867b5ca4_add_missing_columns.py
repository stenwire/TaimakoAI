"""add_missing_columns

Revision ID: ff77867b5ca4
Revises: 35c884792568
Create Date: 2025-12-26 21:20:57.614841

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'ff77867b5ca4'
down_revision: Union[str, Sequence[str], None] = '35c884792568'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Only add the sentiment_score column - don't touch ADK tables (app_states, sessions, events, user_states)
    with op.batch_alter_table('chat_sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sentiment_score', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('chat_sessions', schema=None) as batch_op:
        batch_op.drop_column('sentiment_score')
