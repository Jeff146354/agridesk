from sqlalchemy import Column, Integer, String, JSON
from app.database import Base

class SuratTemplateModel(Base):
    __tablename__ = "surat_templates"

    id = Column(Integer, primary_key=True, index=True)
    jenis = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    fields = Column(JSON, nullable=False)
