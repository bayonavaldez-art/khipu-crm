"""Configuración de pruebas: base de datos de test + cliente HTTP + tokens.

Se usa una base SQLite aparte (test_khipu_crm.db) que se recrea en cada
sesión de pruebas; TestClient ejecuta el lifespan (creación de tablas y seed).
"""
import os

# Debe definirse ANTES de importar la aplicación.
os.environ["DATABASE_URL"] = "sqlite:///./test_khipu_crm.db"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

TEST_DB = "test_khipu_crm.db"


@pytest.fixture(scope="session")
def client():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    with TestClient(app) as c:
        yield c
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def _login(client, username, password):
    resp = client.post("/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture(scope="session")
def admin_headers(client):
    return _login(client, "admin", "Admin@123")


@pytest.fixture(scope="session")
def admision_headers(client):
    return _login(client, "admision", "Admision@123")


@pytest.fixture(scope="session")
def lector_headers(client):
    return _login(client, "lector", "Lector@123")
