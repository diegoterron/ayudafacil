import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 1. Mocking external AI services BEFORE importing the app or services to avoid network/API calls
from app.services.embeddings import embedding_service
from app.services.llm_service import llm_service, AyudaMetadataExtraction, ExtractedAttribute
from app.schemas import VersionSimplificadaSchema

# Mock embeddings to return a fixed vector of length 768 or 1536
EMBED_DIM = len(embedding_service.get_embedding("test")) if hasattr(embedding_service, 'model') else 768
mock_vector = [0.1] * EMBED_DIM

embedding_service.get_embedding = MagicMock(return_value=mock_vector)
embedding_service.get_embeddings = MagicMock(return_value=[mock_vector])

# Mock LLM metadata extraction
mock_metadata = AyudaMetadataExtraction(
    titulo_simplificado="Ayuda Test Mock",
    categoria="Vivienda",
    cuantia="Hasta 1.000 €",
    plazo="2026-12-31",
    sede_link="https://sede.ejemplo.es",
    atributos=[
        ExtractedAttribute(clave="Quién", valor="Inquilinos", icono="👤", color="blue"),
        ExtractedAttribute(clave="Ayuda", valor="Alquiler", icono="🏠", color="green"),
        ExtractedAttribute(clave="Plazo", valor="Abierto", icono="📅", color="orange")
    ],
    es_para_particulares=True,
    es_relevante=True
)
llm_service.extract_metadata = MagicMock(return_value=mock_metadata)

# Mock LLM easy read generation
mock_easy_read = VersionSimplificadaSchema(
    queEs="Esta es una ayuda de prueba simplificada.",
    quienPuedePedir="Personas de prueba.",
    cuantoDan="Te dan una cantidad fija de prueba.",
    plazoComoPedir="Hasta el final del año de prueba."
)
llm_service.generate_easy_read = MagicMock(return_value=mock_easy_read)

# 2. Database setup for testing using SQLite in-memory
from app.database import Base, get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # Create tables in the in-memory SQLite database
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
