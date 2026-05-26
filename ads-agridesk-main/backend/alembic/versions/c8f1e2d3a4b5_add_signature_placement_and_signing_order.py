"""add signature placement and signing order

Revision ID: c8f1e2d3a4b5
Revises: b7e9f2a1c4d8
Create Date: 2026-05-17 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8f1e2d3a4b5'
down_revision: Union[str, None] = 'b7e9f2a1c4d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add signature placement columns
    op.add_column('signatures', sa.Column('page_number', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('signatures', sa.Column('signing_order', sa.Integer(), nullable=True))
    op.add_column('signatures', sa.Column('pos_x', sa.Float(), nullable=True))
    op.add_column('signatures', sa.Column('pos_y', sa.Float(), nullable=True))
    op.add_column('signatures', sa.Column('pos_width', sa.Float(), nullable=True, server_default='120'))
    op.add_column('signatures', sa.Column('pos_height', sa.Float(), nullable=True, server_default='60'))
    op.add_column('signatures', sa.Column('owner_email', sa.String(), nullable=True))

    # Add sequential signing flag to surat
    op.add_column('surat', sa.Column('is_sequential', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('signatures', 'page_number')
    op.drop_column('signatures', 'signing_order')
    op.drop_column('signatures', 'pos_x')
    op.drop_column('signatures', 'pos_y')
    op.drop_column('signatures', 'pos_width')
    op.drop_column('signatures', 'pos_height')
    op.drop_column('signatures', 'owner_email')
    op.drop_column('surat', 'is_sequential')
