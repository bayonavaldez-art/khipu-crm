# Khipu CRM Académico-Comercial

**Seguimiento inteligente de postulantes, alumnos, aliados y proyectos** — Instituto Superior Privado Khipu (Cusco, Perú).

Proyecto final del curso **Desarrollo de Sistemas Inteligentes II** (2025-2).
Estudiante: **Bayona Valdez, Fany** · Docente: **Poma Enrríquez, Genaro Raúl**.

CRM institucional con **módulo de inteligencia artificial**:

- 🎯 **Scoring Predictivo (ML):** calcula la probabilidad de conversión de cada oportunidad a partir de su historial de interacciones, tiempo de respuesta y etapa del embudo (RF02).
- 🤖 **KhipuBot (NLP):** clasifica mensajes entrantes por tipo de contacto (postulante, colegio, empresa, aliado, egresado) y puede crear el contacto automáticamente (RF01).
- 🔔 **Alertas y recomendaciones:** detecta oportunidades sin interacción prolongada y sugiere la próxima acción (RF03).

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| API / Backend | **Python 3.11+ · FastAPI · SQLAlchemy** |
| IA | **scikit-learn** (Regresión Logística + Random Forest, TF-IDF + clasificación de texto) |
| Base de datos | SQLite (desarrollo) / **PostgreSQL** (producción) |
| Frontend | HTML/CSS/JavaScript vanilla + **Chart.js** |
| Autenticación | **JWT** con roles (admin, gestor, admisión, lector) |
| Despliegue | Render / Docker |

> Decisión: un único servicio FastAPI sirve la API del CRM, el módulo de IA y la interfaz web. Simplifica el despliegue sin perder la separación lógica de capas (ver `docs/01-arquitectura.md`).

## Ejecutar localmente

```bash
# 1. Crear entorno virtual e instalar dependencias
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. (Opcional) Re-entrenar los modelos de IA — los artefactos ya están incluidos
python -m ml.generate_dataset      # genera el dataset (4 000+ registros sintéticos)
python -m ml.train_scoring         # entrena y evalúa el scoring
python -m ml.train_nlp             # entrena y evalúa el clasificador NLP

# 3. Levantar el servidor
uvicorn app.main:app --reload
```

- Interfaz web: **http://localhost:8000**
- Documentación de la API (Swagger): **http://localhost:8000/docs**

Usuarios de demostración (se crean automáticamente en el primer arranque):

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `Admin@123` | Administrador (todo) |
| `gestor` | `Gestor@123` | Gestor comercial |
| `admision` | `Admision@123` | Admisión (registra y edita) |
| `lector` | `Lector@123` | Dirección General (solo consulta) |

## Versión desplegada (staging)

<!-- ACTUALIZAR tras el despliegue en Render -->
- App: `https://khipu-crm.onrender.com` *(pendiente)*
- Swagger: `https://khipu-crm.onrender.com/docs`

Pasos para desplegar en `docs/07-despliegue.md`.

## Ejecutar las pruebas

```bash
python -m pytest tests/ -v
```

40 pruebas (unitarias del modelo de IA + funcionales de la API). Plan completo en `docs/04-plan-de-pruebas.md`.

## Estructura del proyecto

```
proyecto-final/
├── app/                    # Backend FastAPI
│   ├── main.py             # Punto de entrada, rutas y archivos estáticos
│   ├── models.py           # Entidades (ORM): Contacto, Interacción, Oportunidad...
│   ├── schemas.py          # Validación de entrada/salida (Pydantic)
│   ├── auth.py             # JWT + hash de contraseñas + control de roles
│   ├── seed.py             # Datos de demostración (primer arranque)
│   └── routers/            # Endpoints: auth, contactos, oportunidades, tareas, dashboard, IA
├── ml/                     # Módulo de Inteligencia Artificial
│   ├── generate_dataset.py # Dataset sintético con nulos/outliers intencionales
│   ├── train_scoring.py    # Entrenamiento + evaluación del scoring predictivo
│   ├── train_nlp.py        # Entrenamiento + evaluación del clasificador KhipuBot
│   ├── service.py          # Carga de artefactos y funciones de inferencia
│   └── artifacts/          # Modelos entrenados + métricas JSON (versionados)
├── static/                 # Interfaz web (login, dashboard, módulos)
├── tests/                  # Pruebas unitarias y funcionales (pytest)
├── docs/                   # Documentación técnica del proyecto
├── Dockerfile
├── docker-compose.yml
├── render.yaml             # Blueprint de despliegue
└── requirements.txt
```

## Documentación

Toda la documentación técnica está en [`docs/`](docs/README.md):

1. [Arquitectura del sistema](docs/01-arquitectura.md)
2. [Modelo de datos](docs/02-modelo-de-datos.md)
3. [Endpoints de la API](docs/03-endpoints.md)
4. [Plan de pruebas](docs/04-plan-de-pruebas.md)
5. [Checklist de seguridad](docs/05-checklist-seguridad.md)
6. [Informe final](docs/06-informe-final.md)
7. [Guía de despliegue](docs/07-despliegue.md)
