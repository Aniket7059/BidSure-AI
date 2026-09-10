"""add file_hash to bid_documents

Revision ID: a1f9c8d7e6b5
Revises: 3da677885b07
Create Date: 2026-09-06 13:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1f9c8d7e6b5'
down_revision: Union[str, Sequence[str], None] = '3da677885b07'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "bid_documents",
        sa.Column(
            "file_hash",
            sa.String(length=64),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "bid_documents",
        "file_hash",
    )
