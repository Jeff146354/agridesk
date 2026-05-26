import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base

# Import all models so they register with Base.metadata
from app.models.user import UserModel  # noqa: F401
from app.models.surat import SuratModel  # noqa: F401
from app.models.signature import SignatureModel  # noqa: F401
from app.models.audit_log import AuditLogModel  # noqa: F401
from app.models.surat_template import SuratTemplateModel  # noqa: F401

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
