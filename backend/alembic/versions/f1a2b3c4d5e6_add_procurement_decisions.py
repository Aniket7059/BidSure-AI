"""add procurement_decisions table

Revision ID: f1a2b3c4d5e6
Revises: e4f5a6b7c8d9
Create Date: 2026-09-07 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'e4f5a6b7c8d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'procurement_decisions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bid_submission_id', sa.Integer(), nullable=False),
        sa.Column('decision', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('decided_by', sa.Integer(), nullable=False),
        sa.Column('decided_at', sa.DateTime(), nullable=False),
        sa.Column('assessment_id', sa.Integer(), nullable=True),
        sa.Column('recommendation_at_decision', sa.String(length=50), nullable=True),
        sa.Column('score_snapshot', sa.Float(), nullable=True),
        sa.Column('risk_snapshot', sa.String(length=50), nullable=True),
        sa.Column('is_override', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['bid_submission_id'], ['bid_submissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['decided_by'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['assessment_id'], ['compliance_assessments.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bid_submission_id', name=op.f('uq_procurement_decisions_bid_submission_id'))
    )
    op.create_index(op.f('ix_procurement_decisions_id'), 'procurement_decisions', ['id'], unique=False)
    op.create_index(op.f('ix_procurement_decisions_bid_submission_id'), 'procurement_decisions', ['bid_submission_id'], unique=True)
    op.create_index(op.f('ix_procurement_decisions_decision'), 'procurement_decisions', ['decision'], unique=False)
    op.create_index(op.f('ix_procurement_decisions_decided_by'), 'procurement_decisions', ['decided_by'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_procurement_decisions_decided_by'), table_name='procurement_decisions')
    op.drop_index(op.f('ix_procurement_decisions_decision'), table_name='procurement_decisions')
    op.drop_index(op.f('ix_procurement_decisions_bid_submission_id'), table_name='procurement_decisions')
    op.drop_index(op.f('ix_procurement_decisions_id'), table_name='procurement_decisions')
    op.drop_table('procurement_decisions')
