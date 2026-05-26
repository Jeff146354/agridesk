import hashlib
import uuid


class HashGenerator:
    @staticmethod
    def generate_hash(data: str) -> str:
        raw = f"{data}:{uuid.uuid4()}"
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def generate_document_hash(surat_id: int, mahasiswa_id: int) -> str:
        raw = f"surat:{surat_id}:mahasiswa:{mahasiswa_id}:{uuid.uuid4()}"
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def verify_hash(data: str, expected_hash: str) -> bool:
        return hashlib.sha256(data.encode()).hexdigest() == expected_hash
