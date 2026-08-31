"""drop unused subscriptions table

Таблица осталась от раннего наброска: писать в неё было некому — подписка
живёт в users (is_subscribed + subscription_expires). Строк в ней нет.

Revision ID: 7f08f0e84186
Revises: a1b2c3d4e5f6
Create Date: 2026-08-31 22:04:19.394411

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '7f08f0e84186'
down_revision: str | None = 'a1b2c3d4e5f6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table('subscriptions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_subscriptions_tg_id'))

    op.drop_table('subscriptions')


def downgrade() -> None:
    op.create_table('subscriptions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tg_id', sa.BigInteger(), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('subscriptions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_subscriptions_tg_id'), ['tg_id'], unique=False)
