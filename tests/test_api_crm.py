"""Pruebas funcionales del CRM: contactos, interacciones, oportunidades,
tareas, alertas y dashboard (RF01-RF03)."""


# ---------- Contactos ----------
def test_crear_y_listar_contacto(client, admision_headers):
    resp = client.post("/contactos", headers=admision_headers, json={
        "nombre": "Juan Prueba Test", "tipo": "empresa",
        "telefono": "987000111", "correo": "juan@test.com",
        "canal_origen": "web", "procedencia": "Prueba automatizada",
    })
    assert resp.status_code == 201
    creado = resp.json()
    assert creado["tipo"] == "empresa"

    lista = client.get("/contactos", headers=admision_headers,
                       params={"q": "Juan Prueba"}).json()
    assert any(c["id"] == creado["id"] for c in lista)


def test_filtro_por_tipo(client, admision_headers):
    lista = client.get("/contactos", headers=admision_headers,
                       params={"tipo": "postulante"}).json()
    assert lista and all(c["tipo"] == "postulante" for c in lista)


def test_contacto_duplicado_no_rompe_api(client, admision_headers):
    # Crear el mismo contacto dos veces está permitido (mismo nombre);
    # lo que no debe pasar es un error 500.
    cuerpo = {"nombre": "Duplicado SA", "tipo": "empresa"}
    assert client.post("/contactos", headers=admision_headers, json=cuerpo).status_code == 201
    assert client.post("/contactos", headers=admision_headers, json=cuerpo).status_code == 201


def test_contacto_inexistente_404(client, admision_headers):
    assert client.get("/contactos/99999", headers=admision_headers).status_code == 404


def test_validacion_tipo_invalido(client, admision_headers):
    resp = client.post("/contactos", headers=admision_headers, json={
        "nombre": "X", "tipo": "extraterrestre",
    })
    assert resp.status_code == 422


def test_correo_invalido_rechazado(client, admision_headers):
    resp = client.post("/contactos", headers=admision_headers, json={
        "nombre": "Correo Malo", "tipo": "empresa", "correo": "no-es-correo",
    })
    assert resp.status_code == 422


def test_eliminar_contacto_solo_admin(client, admision_headers, admin_headers):
    creado = client.post("/contactos", headers=admision_headers, json={
        "nombre": "A Borrar", "tipo": "aliado"}).json()
    # admisión no puede borrar
    assert client.delete(f"/contactos/{creado['id']}", headers=admision_headers).status_code == 403
    # admin sí
    assert client.delete(f"/contactos/{creado['id']}", headers=admin_headers).status_code == 204


# ---------- Interacciones ----------
def test_registrar_interaccion(client, admision_headers):
    creado = client.post("/contactos", headers=admision_headers, json={
        "nombre": "Con Interacción", "tipo": "postulante"}).json()
    resp = client.post(f"/contactos/{creado['id']}/interacciones",
                       headers=admision_headers,
                       json={"tipo": "llamada", "comentario": "Llamada de prueba",
                             "tiempo_respuesta_horas": 3.5})
    assert resp.status_code == 201
    assert resp.json()["tiempo_respuesta_horas"] == 3.5

    historial = client.get(f"/contactos/{creado['id']}/interacciones",
                           headers=admision_headers).json()
    assert len(historial) == 1


# ---------- Oportunidades + Scoring ----------
def test_crear_oportunidad_y_calcular_score(client, admision_headers):
    contacto = client.post("/contactos", headers=admision_headers, json={
        "nombre": "Score Test", "tipo": "postulante",
        "canal_origen": "whatsapp"}).json()
    # historial rico → score alto esperado
    client.post(f"/contactos/{contacto['id']}/interacciones", headers=admision_headers,
                json={"tipo": "mensaje", "comentario": "m1", "tiempo_respuesta_horas": 1.0})
    client.post(f"/contactos/{contacto['id']}/interacciones", headers=admision_headers,
                json={"tipo": "reunion", "comentario": "m2", "tiempo_respuesta_horas": 2.0})

    op = client.post("/oportunidades", headers=admision_headers, json={
        "contacto_id": contacto["id"], "titulo": "Matrícula prueba score",
        "etapa": "negociacion", "monto_estimado": 3000}).json()
    assert op["etapa"] == "negociacion"

    resp = client.post(f"/oportunidades/{op['id']}/score", headers=admision_headers)
    assert resp.status_code == 200
    datos = resp.json()
    assert 0.0 <= datos["probabilidad_conversion"] <= 1.0
    assert datos["recomendacion"]
    # el score queda persistido en la oportunidad
    lista = client.get("/oportunidades", headers=admision_headers,
                       params={"contacto_id": contacto["id"]}).json()
    assert lista[0]["score_ia"] is not None


def test_cambiar_etapa_oportunidad(client, admision_headers):
    ops = client.get("/oportunidades", headers=admision_headers).json()
    op = ops[0]
    resp = client.put(f"/oportunidades/{op['id']}", headers=admision_headers,
                      json={"etapa": "contactado"})
    assert resp.status_code == 200
    assert resp.json()["etapa"] == "contactado"


def test_score_directo_endpoint(client, admision_headers):
    resp = client.post("/ml/score", headers=admision_headers, json={
        "tipo_contacto": "postulante", "canal_origen": "whatsapp",
        "etapa_embudo": "negociacion", "num_interacciones": 6,
        "tiempo_respuesta_promedio": 3.0, "dias_sin_interaccion": 1.0})
    assert resp.status_code == 200
    assert "probabilidad_conversion" in resp.json()
    assert "recomendacion" in resp.json()


# ---------- KhipuBot / NLP ----------
def test_classify_sin_crear(client, admision_headers):
    resp = client.post("/ml/classify", headers=admision_headers, json={
        "mensaje": "Quisiera postular a la carrera de turismo, cuáles son los requisitos"})
    assert resp.status_code == 200
    assert resp.json()["tipo_contacto"] == "postulante"
    assert resp.json()["contacto_id"] is None


def test_classify_crea_contacto(client, admision_headers):
    resp = client.post("/ml/classify", headers=admision_headers, json={
        "mensaje": "Represento a una constructora y buscamos un convenio",
        "crear_contacto": True, "nombre_contacto": "Constructora Test SAC"})
    assert resp.status_code == 200
    assert resp.json()["contacto_id"] is not None


# ---------- Tareas y alertas ----------
def test_crear_y_completar_tarea(client, admision_headers):
    tarea = client.post("/tareas", headers=admision_headers, json={
        "titulo": "Tarea de prueba automatizada"}).json()
    assert tarea["estado"] == "pendiente"

    resp = client.put(f"/tareas/{tarea['id']}/completar", headers=admision_headers)
    assert resp.status_code == 200
    assert resp.json()["estado"] == "hecha"


def test_alertas_funcionan(client, admision_headers):
    resp = client.get("/alertas", headers=admision_headers)
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert "total" in cuerpo and isinstance(cuerpo["alertas"], list)
    # en los datos demo existe al menos una oportunidad vieja sin interacción
    assert cuerpo["total"] >= 1


def test_dashboard_resumen(client, admision_headers):
    resp = client.get("/dashboard", headers=admision_headers)
    assert resp.status_code == 200
    d = resp.json()
    assert d["total_contactos"] > 0
    assert set(d["embudo"].keys()) == {"nuevo", "contactado", "negociacion", "ganado", "perdido"}
    assert 0 <= d["tasa_conversion_pct"] <= 100


def test_campanas(client, admision_headers):
    resp = client.post("/campanas", headers=admision_headers, json={
        "nombre": "Campaña de prueba", "objetivo": "Validar API"})
    assert resp.status_code == 201
    assert client.get("/campanas", headers=admision_headers).json()


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"
