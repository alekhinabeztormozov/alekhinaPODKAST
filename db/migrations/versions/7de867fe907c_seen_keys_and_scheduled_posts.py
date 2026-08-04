"""seen keys and scheduled posts

Revision ID: 7de867fe907c
Revises: eb1a8d828e89
Create Date: 2026-08-04 12:51:51.086794

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '7de867fe907c'
down_revision: str | None = 'eb1a8d828e89'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('scheduled_posts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('target', sa.String(length=128), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('publish_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('scheduled_posts', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_scheduled_posts_publish_at'), ['publish_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_scheduled_posts_status'), ['status'], unique=False)

    op.create_table('seen_keys',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('kind', sa.String(length=32), nullable=False),
    sa.Column('key', sa.String(length=512), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('kind', 'key', name='uq_seen_kind_key')
    )
    with op.batch_alter_table('seen_keys', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_seen_keys_kind'), ['kind'], unique=False)



def downgrade() -> None:
    with op.batch_alter_table('seen_keys', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_seen_keys_kind'))

    op.drop_table('seen_keys')
    with op.batch_alter_table('scheduled_posts', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_scheduled_posts_status'))
        batch_op.drop_index(batch_op.f('ix_scheduled_posts_publish_at'))

    op.drop_table('scheduled_posts')
