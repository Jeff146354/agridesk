import enum


class UserRole(str, enum.Enum):
    MAHASISWA = "MAHASISWA"
    DOSEN = "DOSEN"
    ADMIN = "ADMIN"


class SuratStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    MENUNGGU_TTD_DOSEN = "MENUNGGU_TTD_DOSEN"
    MENUNGGU_PROSES_ADMIN = "MENUNGGU_PROSES_ADMIN"
    SELESAI = "SELESAI"
    DITOLAK = "DITOLAK"
