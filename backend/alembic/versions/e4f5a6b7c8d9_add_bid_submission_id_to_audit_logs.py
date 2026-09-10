"""add bid_submission_id to audit_logs

Revision ID: e4f5a6b7c8d9
Revises: c7d8e9f0a1b2
Create Date: 2026-09-07 20:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e4f5a6b7c8d9'
down_revision: Union[str, Sequence[str], None] = 'c7d8e9f0a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('audit_logs', sa.Column('bid_submission_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_audit_logs_bid_submission_id'), 'audit_logs', ['bid_submission_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_logs_bid_submission_id'), table_name='audit_logs')
    op.drop_column('audit_logs', 'bid_submission_id')
