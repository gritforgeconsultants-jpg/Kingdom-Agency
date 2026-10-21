"""add xp column to child_profiles

Revision ID: a3f7c8e91d02
Revises: 1b232b1a4f84
Create Date: 2026-10-21 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3f7c8e91d02'
down_revision: Union[str, None] = '1b232b1a4f84'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'child_profiles',
        sa.Column('xp', sa.Integer(), nullable=False, server_default='0'),
    )


def downgrade() -> None:
    op.drop_column('child_profiles', 'xp')
