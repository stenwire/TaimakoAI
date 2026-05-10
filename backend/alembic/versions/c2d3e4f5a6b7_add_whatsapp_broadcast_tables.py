"""add whatsapp broadcast tables

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-04-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, None] = '266444da8a8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'whatsapp_contacts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('business_id', sa.String(), nullable=False),
        sa.Column('phone_e164', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('source', sa.String(), nullable=False, server_default='manual'),
        sa.Column('opted_in', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('last_contacted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('business_id', 'phone_e164', name='uq_whatsapp_contacts_business_phone'),
    )
    op.create_index(
        'ix_whatsapp_contacts_business_id', 'whatsapp_contacts', ['business_id']
    )

    op.create_table(
        'whatsapp_contact_lists',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('business_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_whatsapp_contact_lists_business_id', 'whatsapp_contact_lists', ['business_id']
    )

    op.create_table(
        'whatsapp_contact_list_members',
        sa.Column('contact_list_id', sa.String(), nullable=False),
        sa.Column('contact_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['contact_id'], ['whatsapp_contacts.id']),
        sa.ForeignKeyConstraint(['contact_list_id'], ['whatsapp_contact_lists.id']),
        sa.PrimaryKeyConstraint('contact_list_id', 'contact_id'),
    )

    op.create_table(
        'whatsapp_templates',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('business_id', sa.String(), nullable=False),
        sa.Column('meta_template_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('language', sa.String(), nullable=False, server_default='en_US'),
        sa.Column('header', sa.JSON(), nullable=True),
        sa.Column('body_text', sa.Text(), nullable=False),
        sa.Column('footer', sa.String(), nullable=True),
        sa.Column('buttons', sa.JSON(), nullable=True),
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='DRAFT'),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('source', sa.String(), nullable=False, server_default='CREATED'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'business_id', 'name', 'language', name='uq_whatsapp_templates_business_name_lang'
        ),
    )
    op.create_index(
        'ix_whatsapp_templates_business_id', 'whatsapp_templates', ['business_id']
    )
    op.create_index(
        'ix_whatsapp_templates_meta_template_id', 'whatsapp_templates', ['meta_template_id']
    )

    op.create_table(
        'whatsapp_campaigns',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('business_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('template_id', sa.String(), nullable=False),
        sa.Column('audience_type', sa.String(), nullable=False),
        sa.Column('audience_ref', sa.JSON(), nullable=True),
        sa.Column('variable_mapping', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='DRAFT'),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('total_recipients', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sent_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('delivered_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('read_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_by_user_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id']),
        sa.ForeignKeyConstraint(['template_id'], ['whatsapp_templates.id']),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_whatsapp_campaigns_business_id', 'whatsapp_campaigns', ['business_id']
    )
    op.create_index(
        'ix_whatsapp_campaigns_status', 'whatsapp_campaigns', ['status']
    )
    op.create_index(
        'ix_whatsapp_campaigns_scheduled_at', 'whatsapp_campaigns', ['scheduled_at']
    )

    op.create_table(
        'whatsapp_campaign_messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('campaign_id', sa.String(), nullable=False),
        sa.Column('contact_phone', sa.String(), nullable=False),
        sa.Column('variables_snapshot', sa.JSON(), nullable=True),
        sa.Column('meta_message_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='QUEUED'),
        sa.Column('error_code', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['whatsapp_campaigns.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'campaign_id', 'contact_phone', name='uq_whatsapp_campaign_messages_campaign_phone'
        ),
    )
    op.create_index(
        'ix_whatsapp_campaign_messages_campaign_id',
        'whatsapp_campaign_messages',
        ['campaign_id'],
    )
    op.create_index(
        'ix_whatsapp_campaign_messages_meta_id',
        'whatsapp_campaign_messages',
        ['meta_message_id'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_whatsapp_campaign_messages_meta_id', table_name='whatsapp_campaign_messages')
    op.drop_index('ix_whatsapp_campaign_messages_campaign_id', table_name='whatsapp_campaign_messages')
    op.drop_table('whatsapp_campaign_messages')

    op.drop_index('ix_whatsapp_campaigns_scheduled_at', table_name='whatsapp_campaigns')
    op.drop_index('ix_whatsapp_campaigns_status', table_name='whatsapp_campaigns')
    op.drop_index('ix_whatsapp_campaigns_business_id', table_name='whatsapp_campaigns')
    op.drop_table('whatsapp_campaigns')

    op.drop_index('ix_whatsapp_templates_meta_template_id', table_name='whatsapp_templates')
    op.drop_index('ix_whatsapp_templates_business_id', table_name='whatsapp_templates')
    op.drop_table('whatsapp_templates')

    op.drop_table('whatsapp_contact_list_members')

    op.drop_index('ix_whatsapp_contact_lists_business_id', table_name='whatsapp_contact_lists')
    op.drop_table('whatsapp_contact_lists')

    op.drop_index('ix_whatsapp_contacts_business_id', table_name='whatsapp_contacts')
    op.drop_table('whatsapp_contacts')
