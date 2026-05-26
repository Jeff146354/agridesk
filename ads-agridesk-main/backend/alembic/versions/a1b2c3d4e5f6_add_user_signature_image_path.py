"""add_user_signature_image_path

Revision ID: a1b2c3d4e5f6
Revises: 7c2a9f3b1e11
Create Date: 2026-03-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "7c2a9f3b1e11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("signature_image_path", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "signature_image_path")
