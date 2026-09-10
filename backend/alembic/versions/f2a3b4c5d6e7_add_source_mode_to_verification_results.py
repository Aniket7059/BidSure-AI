"""add source_mode to verification_results table

Revision ID: f2a3b4c5d6e7
Revises: f1a2b3c4d5e6
Create Date: 2026-09-08 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f2a3b4c5d6e7'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'verification_results',
        sa.Column('source_mode', sa.String(length=50), nullable=False, server_default='SYNTHETIC')
    )
    op.create_index(
        op.f('ix_verification_results_source_mode'),
        'verification_results',
        ['source_mode'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_verification_results_source_mode'), table_name='verification_results')
    op.drop_column('verification_results', 'source_mode')
