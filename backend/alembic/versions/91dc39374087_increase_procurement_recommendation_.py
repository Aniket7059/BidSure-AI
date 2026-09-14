"""increase procurement recommendation length

Revision ID: 91dc39374087
Revises: 888a10962318
Create Date: 2026-09-13 18:38:49.250209

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91dc39374087'
down_revision: Union[str, Sequence[str], None] = "888a10962318"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column(
        "procurement_decisions",
        "recommendation_at_decision",
        existing_type=sa.String(length=50),
        type_=sa.String(length=1000),
        existing_nullable=True,
    )


def downgrade():
    op.alter_column(
        "procurement_decisions",
        "recommendation_at_decision",
        existing_type=sa.String(length=1000),
        type_=sa.String(length=50),
        existing_nullable=True,
    )