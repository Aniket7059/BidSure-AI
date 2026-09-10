"""add discrepancies table

Revision ID: c7d8e9f0a1b2
Revises: a1f9c8d7e6b5
Create Date: 2026-09-07 14:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, Sequence[str], None] = 'a1f9c8d7e6b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'discrepancies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bid_submission_id', sa.Integer(), nullable=False),
        sa.Column('tender_requirement_id', sa.Integer(), nullable=True),
        sa.Column('bid_document_id', sa.Integer(), nullable=True),
        sa.Column('verification_result_id', sa.Integer(), nullable=True),
        sa.Column('compliance_check_id', sa.Integer(), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='MEDIUM'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='OPEN'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('expected_value', sa.Text(), nullable=True),
        sa.Column('observed_value', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='CROSS_VERIFICATION'),
        sa.Column('evidence', sa.JSON(), nullable=True),
        sa.Column('finding_key', sa.String(length=255), nullable=True),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['bid_submission_id'], ['bid_submissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tender_requirement_id'], ['tender_requirements.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['bid_document_id'], ['bid_documents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['verification_result_id'], ['verification_results.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['compliance_check_id'], ['compliance_checks.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_discrepancies_id'), 'discrepancies', ['id'], unique=False)
    op.create_index(op.f('ix_discrepancies_bid_submission_id'), 'discrepancies', ['bid_submission_id'], unique=False)
    op.create_index(op.f('ix_discrepancies_tender_requirement_id'), 'discrepancies', ['tender_requirement_id'], unique=False)
    op.create_index(op.f('ix_discrepancies_bid_document_id'), 'discrepancies', ['bid_document_id'], unique=False)
    op.create_index(op.f('ix_discrepancies_verification_result_id'), 'discrepancies', ['verification_result_id'], unique=False)
    op.create_index(op.f('ix_discrepancies_compliance_check_id'), 'discrepancies', ['compliance_check_id'], unique=False)
    op.create_index(op.f('ix_discrepancies_type'), 'discrepancies', ['type'], unique=False)
    op.create_index(op.f('ix_discrepancies_severity'), 'discrepancies', ['severity'], unique=False)
    op.create_index(op.f('ix_discrepancies_status'), 'discrepancies', ['status'], unique=False)
    op.create_index(op.f('ix_discrepancies_finding_key'), 'discrepancies', ['finding_key'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_discrepancies_finding_key'), table_name='discrepancies')
    op.drop_index(op.f('ix_discrepancies_status'), table_name='discrepancies')
    op.drop_index(op.f('ix_discrepancies_severity'), table_name='discrepancies')
    op.drop_index(op.f('ix_discrepancies_type'), table_name='discrepancies')
    op.drop_index(op.f('ix_discrepancies_compliance_check_id'), table_name='discrepancies')
    op.drop_index(op.f('ix_discrepancies_verification_result_id'), table_name='discrepancies')
    op.drop_index(op.f('ix_discrepancies_bid_document_id'), table_name='discrepancies')
    op.drop_index(op.f('ix_discrepancies_tender_requirement_id'), table_name='discrepancies')
    op.drop_index(op.f('ix_discrepancies_bid_submission_id'), table_name='discrepancies')
    op.drop_index(op.f('ix_discrepancies_id'), table_name='discrepancies')
    op.drop_table('discrepancies')
