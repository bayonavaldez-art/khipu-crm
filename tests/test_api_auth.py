"""Pruebas funcionales: autenticación y control de roles (RNF01)."""


def test_login_correcto(client, admin_headers):
    resp = client.get("/auth/me", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["rol"] == "admin"


def test_login_password_incorrecta(client):
    resp = client.post("/auth/login", json={"username": "admin", "password": "malaclave"})
    assert resp.status_code == 401


def test_login_usuario_inexistente(client):
    resp = client.post("/auth/login", json={"username": "nadie", "password": "clave123"})
    assert resp.status_code == 401


def test_login_validacion_input(client):
    # Contraseña demasiado corta: rechazada por validación (422).
    resp = client.post("/auth/login", json={"username": "ab", "password": "123"})
    assert resp.status_code == 422


def test_endpoints_protegidos_sin_token(client):
    for ruta in ["/contactos", "/oportunidades", "/tareas", "/dashboard", "/ml/model-info"]:
        assert client.get(ruta).status_code == 401, ruta


def test_token_invalido_rechazado(client):
    resp = client.get("/contactos", headers={"Authorization": "Bearer falso.token.aqui"})
    assert resp.status_code == 401


def test_lector_no_puede_crear(client, lector_headers):
    resp = client.post("/contactos", headers=lector_headers, json={
        "nombre": "Prueba Lector", "tipo": "postulante",
    })
    assert resp.status_code == 403


def test_lector_puede_consultar(client, lector_headers):
    assert client.get("/contactos", headers=lector_headers).status_code == 200


def test_admision_puede_crear(client, admision_headers):
    resp = client.post("/contactos", headers=admision_headers, json={
        "nombre": "Prueba Admisión", "tipo": "postulante",
        "correo": "prueba@khipu.edu.pe",
    })
    assert resp.status_code == 201
