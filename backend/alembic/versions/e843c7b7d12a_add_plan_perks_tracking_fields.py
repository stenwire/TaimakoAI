"""add_plan_perks_tracking_fields

Revision ID: e843c7b7d12a
Revises: d88681a7b3d0
Create Date: 2026-03-02 22:25:47.306193

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e843c7b7d12a'
down_revision: Union[str, Sequence[str], None] = 'd88681a7b3d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('businesses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('allocated_ai_responses', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('used_ai_responses', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('allocated_escalations', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('used_escalations', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('allocated_messages_per_session', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('allocated_daily_sessions', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('allocated_whitelisted_domains', sa.Integer(), nullable=False, server_default='0'))

    # Data migration
    op.execute("""
        UPDATE businesses
        SET allocated_ai_responses = credits_balance,
            used_ai_responses = 0,
            allocated_escalations = CASE
                WHEN subscription_tier = 'nexus' THEN 500
                WHEN subscription_tier = 'flux' THEN 50
                ELSE 5
            END,
            used_escalations = total_escalations_used,
            allocated_messages_per_session = CASE
                WHEN subscription_tier = 'nexus' THEN 100
                WHEN subscription_tier = 'flux' THEN 50
                ELSE 20
            END,
            allocated_daily_sessions = CASE
                WHEN subscription_tier = 'nexus' THEN 5000
                WHEN subscription_tier = 'flux' THEN 500
                ELSE 50
            END,
            allocated_whitelisted_domains = CASE
                WHEN subscription_tier = 'nexus' THEN 10
                WHEN subscription_tier = 'flux' THEN 3
                ELSE 1
            END
    """)

    with op.batch_alter_table('businesses', schema=None) as batch_op:
        batch_op.drop_column('total_escalations_used')
        batch_op.drop_column('credits_balance')


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('businesses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('credits_balance', sa.INTEGER(), server_default=sa.text('100'), autoincrement=False, nullable=False))
        batch_op.add_column(sa.Column('total_escalations_used', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=False))

    # Data Migration backwards
    op.execute("""
        UPDATE businesses
        SET credits_balance = allocated_ai_responses - used_ai_responses,
            total_escalations_used = used_escalations
    """)
    op.execute("UPDATE businesses SET credits_balance = 0 WHERE credits_balance < 0")

    with op.batch_alter_table('businesses', schema=None) as batch_op:
        batch_op.drop_column('allocated_whitelisted_domains')
        batch_op.drop_column('allocated_daily_sessions')
        batch_op.drop_column('allocated_messages_per_session')
        batch_op.drop_column('used_escalations')
        batch_op.drop_column('allocated_escalations')
        batch_op.drop_column('used_ai_responses')
        batch_op.drop_column('allocated_ai_responses')
