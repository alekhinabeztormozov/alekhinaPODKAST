"""reels conveyor table

Revision ID: b7e2c4d9a1f0
Revises: 7f08f0e84186
Create Date: 2026-10-25 20:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'b7e2c4d9a1f0'
down_revision: str | None = '7f08f0e84186'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'reels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('episode_ref', sa.String(length=128), nullable=False),
        sa.Column('episode_title', sa.String(length=512), nullable=False, server_default=''),
        sa.Column('kind', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False, server_default='draft'),
        sa.Column('scenario', sa.JSON(), nullable=False),
        sa.Column('feedback', sa.Text(), nullable=False, server_default=''),
        sa.Column('render_job', sa.String(length=128), nullable=False, server_default=''),
        sa.Column('track_path', sa.Text(), nullable=False, server_default=''),
        sa.Column('video_path', sa.Text(), nullable=False, server_default=''),
        sa.Column('publish_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published', sa.JSON(), nullable=False),
        sa.Column('error', sa.Text(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_reels_episode_ref'), 'reels', ['episode_ref'], unique=False)
    op.create_index(op.f('ix_reels_status'), 'reels', ['status'], unique=False)
    op.create_index(op.f('ix_reels_publish_at'), 'reels', ['publish_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_reels_publish_at'), table_name='reels')
    op.drop_index(op.f('ix_reels_status'), table_name='reels')
    op.drop_index(op.f('ix_reels_episode_ref'), table_name='reels')
    op.drop_table('reels')
