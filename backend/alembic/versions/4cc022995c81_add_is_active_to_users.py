"""add is_active to users

Revision ID: 4cc022995c81
Revises: f2a3b4c5d6e7
Create Date: 2026-09-13 16:51:02.334287

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4cc022995c81'
down_revision: Union[str, Sequence[str], None] = 'f2a3b4c5d6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('true'),
        ),
    )



def downgrade() -> None:
    op.drop_column('users', 'is_active')
