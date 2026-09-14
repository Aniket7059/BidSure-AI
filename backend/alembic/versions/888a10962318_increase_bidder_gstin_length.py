"""increase bidder gstin length

Revision ID: 888a10962318
Revises: 4cc022995c81
Create Date: 2026-09-13 17:16:18.442309

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '888a10962318'
down_revision: Union[str, Sequence[str], None] = '4cc022995c81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column(
        "bidders",
        "gstin",
        existing_type=sa.String(length=15),
        type_=sa.String(length=50),
        existing_nullable=True,
    )
   


def downgrade():
    op.alter_column(
        "bidders",
        "gstin",
        existing_type=sa.String(length=50),
        type_=sa.String(length=15),
        existing_nullable=True,
    )