# 4. Plan de pruebas

## 4.1 Estrategia

Dos niveles, alineados a la rúbrica del curso (criterio "Pruebas" 15 %):

| Nivel | Alcance | Herramienta | Archivo |
|---|---|---|---|
| Unitarias | modelo de IA: métricas mínimas, coherencia de predicciones, NLP | pytest | `tests/test_modelo_ia.py` |
| Funcionales (API) | auth, roles, CRUD, interacciones, scoring, alertas, dashboard | pytest + TestClient (httpx) | `tests/test_api_auth.py`, `tests/test_api_crm.py` |

La base de datos de pruebas es un SQLite aparte (`test_khipu_crm.db`) que se
recrea en cada sesión; el cliente de pruebas levanta la aplicación completa
(lifespan incluido) sobre esa base.

## 4.2 Casos unitarios — modelo de IA

| ID | Caso | Criterio de aprobación |
|---|---|---|
| U01 | Artefactos entrenados existen | `scoring_model.joblib` y `nlp_model.joblib` presentes |
| U02 | Métricas del scoring superan umbral | accuracy ≥ 0.75, F1 ≥ 0.70, ROC-AUC ≥ 0.80 |
| U03 | Métricas del NLP superan umbral | accuracy ≥ 0.85, F1 macro ≥ 0.85 |
| U04 | Coherencia del scoring | respuesta rápida + etapa avanzada ⇒ mayor probabilidad que respuesta lenta + etapa inicial |
| U05 | Rango válido de probabilidades | toda predicción ∈ [0, 1] |
| U06 | Recomendaciones coherentes | score alto ⇒ "entrevista/cierre"; score bajo + días ⇒ "reactivar/perdido" |
| U07-U10 | Clasificación NLP por clase | postulante, empresa, colegio y egresado correctamente clasificados |
| U11 | Rendimiento del scoring (RNF02) | 100 scores en < 3 s |

## 4.3 Casos funcionales — API

| ID | Caso | Criterio de aprobación |
|---|---|---|
| F01 | Login correcto | 200 + token + rol |
| F02/F03 | Password incorrecta / usuario inexistente | 401 sin revelar cuál campo falló |
| F04 | Validación de inputs en login | 422 ante campos fuera de rango |
| F05 | Endpoints protegidos sin token | 401 en /contactos, /oportunidades, /tareas, /dashboard, /ml |
| F06 | Token inválido | 401 |
| F07 | Rol lector no puede crear | 403 |
| F08 | Rol lector puede consultar | 200 |
| F09 | Rol admisión crea contacto | 201 |
| F10 | Crear + buscar contacto por nombre | el contacto aparece en la búsqueda |
| F11 | Filtro por tipo | todos los resultados del tipo pedido |
| F12 | Operaciones repetidas no rompen la API | 201, sin error 500 |
| F13 | Recurso inexistente | 404 |
| F14/F15 | Tipo inválido / correo inválido | 422 |
| F16 | Eliminar contacto: admisión no, admin sí | 403 / 204 |
| F17 | Registrar interacción y ver historial | 201 y lista con 1 registro |
| F18 | Crear oportunidad y calcular score | probabilidad ∈ [0,1], recomendación presente, score persistido |
| F19 | Cambiar etapa de oportunidad | etapa actualizada |
| F20 | Scoring directo `/ml/score` | 200 con probabilidad y recomendación |
| F21 | KhipuBot clasifica sin crear | tipo correcto, `contacto_id` null |
| F22 | KhipuBot clasifica y crea contacto | `contacto_id` presente |
| F23 | Crear y completar tarea | pendiente → hecha |
| F24 | Alertas de seguimiento | estructura válida y ≥ 1 alerta en datos demo |
| F25 | Dashboard | embudo completo, tasa de conversión ∈ [0,100] |
| F26 | Campañas | crear y listar |
| F27 | Healthcheck | `{"status":"ok"}` |

## 4.4 Evidencia de ejecución

```
$ python -m pytest tests/ -v
============================ 38 passed in 1.30s ============================
```

- Total: **38 pruebas aprobadas** (11 unitarias del modelo + 27 funcionales).
- Las 2 advertencias mostradas son deprecations internas de librerías
  (starlette/anyio), no afectan los resultados.
- La ejecución completa tarda ~1.5 s.

*Adjuntar captura de la terminal al informe PDF final (evidencia).*

## 4.5 Prueba de rendimiento (RNF02)

La prueba U11 mide el tiempo de 100 inferencias del modelo de scoring
resultado < 3 s en total, muy por debajo del requisito de 3 s por consulta
con hasta 10 000 contactos. El modelo se carga en memoria una única vez
(singleton), por lo que cada llamada solo paga el costo de la predicción.

## 4.6 Cómo reproducir

```bash
source .venv/bin/activate
python -m pytest tests/ -v          # todo
python -m pytest tests/test_modelo_ia.py -v   # solo unitarias
python -m pytest tests/test_api_crm.py -v     # solo funcionales
```
