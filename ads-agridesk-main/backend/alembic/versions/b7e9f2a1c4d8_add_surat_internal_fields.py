"""add_surat_internal_fields

Revision ID: b7e9f2a1c4d8
Revises: a1b2c3d4e5f6
Create Date: 2026-03-09 13:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7e9f2a1c4d8"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("surat", sa.Column("internal_fields", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("surat", "internal_fields")
