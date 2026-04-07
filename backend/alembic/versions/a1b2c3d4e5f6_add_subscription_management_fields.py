"""Add subscription management fields

Revision ID: a1b2c3d4e5f6
Revises: 538ca2f1a3cf
Create Date: 2026-02-22 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '538ca2f1a3cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add fields for subscription management: authorization_code, email_token, last_payment_date, interval."""
    with op.batch_alter_table('businesses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('authorization_code', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('subscription_email_token', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('last_payment_date', sa.DateTime(), nullable=True))

    with op.batch_alter_table('plans', schema=None) as batch_op:
        batch_op.add_column(sa.Column('interval', sa.String(), nullable=False, server_default='monthly'))


def downgrade() -> None:
    """Remove subscription management fields."""
    with op.batch_alter_table('plans', schema=None) as batch_op:
        batch_op.drop_column('interval')

    with op.batch_alter_table('businesses', schema=None) as batch_op:
        batch_op.drop_column('last_payment_date')
        batch_op.drop_column('subscription_email_token')
        batch_op.drop_column('authorization_code')
