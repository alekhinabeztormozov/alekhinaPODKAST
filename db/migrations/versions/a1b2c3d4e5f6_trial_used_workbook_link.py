"""trial_used on users, workbook_link on seasons

Revision ID: a1b2c3d4e5f6
Revises: 7d380a9c3130
Create Date: 2026-08-16 13:10:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: str | None = '7d380a9c3130'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('trial_used', sa.Boolean(), nullable=False, server_default=sa.false())
        )
    with op.batch_alter_table('seasons', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('workbook_link', sa.Text(), nullable=False, server_default='')
        )


def downgrade() -> None:
    with op.batch_alter_table('seasons', schema=None) as batch_op:
        batch_op.drop_column('workbook_link')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('trial_used')
