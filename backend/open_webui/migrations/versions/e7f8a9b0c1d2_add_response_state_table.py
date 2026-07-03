"""Add response_state table

Revision ID: e7f8a9b0c1d2
Revises: 42e2978c7933
Create Date: 2026-07-03 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'e7f8a9b0c1d2'
down_revision: Union[str, None] = '42e2978c7933'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    if 'response_state' not in existing_tables:
        op.create_table(
            'response_state',
            sa.Column('id', sa.Text(), primary_key=True),
            sa.Column('user_id', sa.Text(), nullable=False),
            sa.Column('chat_id', sa.Text(), nullable=False),
            sa.Column('message_id', sa.Text(), nullable=False),
            sa.Column('model', sa.Text(), nullable=False),
            sa.Column('status', sa.Text(), nullable=False, server_default='completed'),
            sa.Column('input', sa.Text(), nullable=True),
            sa.Column('instructions', sa.Text(), nullable=True),
            sa.Column('output', sa.Text(), nullable=True),
            sa.Column('response', sa.Text(), nullable=True),
            sa.Column('usage', sa.Text(), nullable=True),
            sa.Column('meta', sa.Text(), nullable=True),
            sa.Column('store', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('created_at', sa.BigInteger(), nullable=False),
            sa.Column('updated_at', sa.BigInteger(), nullable=False),
        )
        op.create_index('ix_response_state_user_id', 'response_state', ['user_id'])
        op.create_index('ix_response_state_chat_id', 'response_state', ['chat_id'])
        op.create_index('ix_response_state_model', 'response_state', ['model'])
        op.create_index('ix_response_state_created_at', 'response_state', ['created_at'])
        op.create_index('response_state_user_created_idx', 'response_state', ['user_id', 'created_at'])
        op.create_index('response_state_chat_message_idx', 'response_state', ['chat_id', 'message_id'])


def downgrade() -> None:
    op.drop_table('response_state')
