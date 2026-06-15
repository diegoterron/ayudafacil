import pytest
from app.models import Ayuda, Usuario

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "AyudaFácil Backend"}

def test_user_registration_and_login_flow(client):
    """Test full user authentication flow: register, duplicate register, login, and profile update."""
    # 1. Register a new user
    reg_payload = {
        "username": "tester",
        "password": "securepassword",
        "role": "ciudadano"
    }
    response = client.post("/api/auth/register", json=reg_payload)
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["username"] == "tester"
    assert user_data["role"] == "ciudadano"
    assert "password_hash" not in user_data
    assert user_data["accessibility_profile"] == "standard"
    user_id = user_data["id"]

    # 2. Try to register with duplicate username
    response = client.post("/api/auth/register", json=reg_payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "El nombre de usuario ya está registrado"

    # 3. Login with correct credentials
    login_payload = {
        "username": "tester",
        "password": "securepassword"
    }
    response = client.post("/api/auth/login", json=login_payload)
    assert response.status_code == 200
    assert response.json()["id"] == user_id

    # 4. Login with incorrect credentials
    bad_login_payload = {
        "username": "tester",
        "password": "wrongpassword"
    }
    response = client.post("/api/auth/login", json=bad_login_payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Credenciales incorrectas"

    # 5. Update user accessibility profile
    profile_payload = {
        "accessibility_profile": "easy"
    }
    response = client.put(f"/api/users/{user_id}/profile", json=profile_payload)
    assert response.status_code == 200
    assert response.json()["accessibility_profile"] == "easy"


def test_search_ayudas_lexical_fallback(client, db_session):
    """Test search endpoint with a seeded aid. Verifies lexical search fallback works in SQLite."""
    # Seed an Ayuda in the database
    new_ayuda = Ayuda(
        codigo_bdns="123456",
        titulo="Subvención de prueba para alquiler de vivienda",
        titulo_simplificado="Ayuda alquiler",
        organismo="Ministerio de Vivienda",
        categoria="Vivienda",
        cuantia="Hasta 500 €",
        plazo=None,
        plazo_abierto=True,
        es_para_particulares=True,
        es_relevante=True,
        sede_link="http://sede.vivienda.es",
        boe_link="http://boe.es",
        descripcion_oficial="Esta ayuda está destinada a personas físicas para financiar parte del alquiler...",
        atributos_json=[{"clave": "Quién", "valor": "Inquilinos", "icono": "👤", "color": "blue"}],
        lectura_facil_json={
            "queEs": "Dinero para tu alquiler.",
            "quienPuedePedir": "Personas de alquiler.",
            "cuantoDan": "Hasta 500 euros.",
            "plazoComoPedir": "Plazo abierto."
        }
    )
    db_session.add(new_ayuda)
    db_session.commit()

    # Query the search endpoint
    response = client.get("/api/search?q=alquiler")
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert results[0]["codigo_bdns"] == "123456"
    # The database query to vector search fails in SQLite, so degraded_service should be True
    assert results[0]["degraded_service"] is True


def test_get_ayuda_detail_with_generation(client, db_session):
    """Test retrieving help details and generating easy read simplification on the fly if missing."""
    # Seed an Ayuda without lectura_facil_json
    new_ayuda = Ayuda(
        codigo_bdns="987654",
        titulo="Ayuda oficial sin simplificar",
        titulo_simplificado=None,
        organismo="Gobierno de España",
        categoria="Social",
        cuantia="Variable",
        plazo=None,
        plazo_abierto=True,
        es_para_particulares=True,
        es_relevante=True,
        sede_link="http://sede.gob.es",
        boe_link="http://boe.es",
        descripcion_oficial="Extracto de BOE con muchos tecnicismos y palabras administrativas complejas...",
        atributos_json=[],
        lectura_facil_json=None # Force generation on the fly
    )
    db_session.add(new_ayuda)
    db_session.commit()
    db_session.refresh(new_ayuda)

    # Fetch detail
    response = client.get(f"/api/ayudas/{new_ayuda.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["codigo_bdns"] == "987654"
    assert data["version_simplificada"] is not None
    assert data["version_simplificada"]["queEs"] == "Esta es una ayuda de prueba simplificada."

    # Check that it got saved in the database
    updated_ayuda = db_session.query(Ayuda).filter(Ayuda.id == new_ayuda.id).first()
    assert updated_ayuda.lectura_facil_json is not None
    assert updated_ayuda.lectura_facil_json["queEs"] == "Esta es una ayuda de prueba simplificada."
