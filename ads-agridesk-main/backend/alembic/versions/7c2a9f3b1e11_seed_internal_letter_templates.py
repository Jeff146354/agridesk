"""seed_internal_letter_templates

Revision ID: 7c2a9f3b1e11
Revises: 3fa6d8068165
Create Date: 2026-03-09 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7c2a9f3b1e11"
down_revision: Union[str, None] = "3fa6d8068165"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    templates = sa.table(
        "letter_templates",
        sa.column("name", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("template_path", sa.String()),
        sa.column("required_fields", sa.Text()),
    )

    op.bulk_insert(
        templates,
        [
            {
                "name": "Surat Keterangan Aktif Kuliah",
                "description": "Surat untuk membuktikan status aktif kuliah mahasiswa.",
                "template_path": "templates/surat_keterangan_aktif_kuliah.pdf",
                "required_fields": '["keperluan_surat_aktif"]',
            },
            {
                "name": "Surat Pembatalan Mata Kuliah",
                "description": "Surat pengajuan pembatalan mata kuliah tertentu.",
                "template_path": "templates/surat_pembatalan_mata_kuliah.pdf",
                "required_fields": '["mata_kuliah_yang_dibatalkan", "alasan_pembatalan_kuliah"]',
            },
        ],
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM letter_templates WHERE name IN ("
        "'Surat Keterangan Aktif Kuliah', 'Surat Pembatalan Mata Kuliah'"
        ")"
    )
