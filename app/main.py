"""Khipu CRM Académico-Comercial — API REST (FastAPI).

Punto de entrada de la aplicación:
  - Expone la API del CRM (contactos, interacciones, oportunidades, tareas).
  - Expone el módulo de IA (scoring predictivo y clasificación NLP).
  - Sirve la interfaz web estática (static/).
  - Documentación interactiva: /docs (Swagger) y /redoc.

Ejecución local:  uvicorn app.main:app --reload
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import Base, engine, SessionLocal
from app.routers import auth_router, contactos, dashboard, ml, oportunidades, tareas

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crea tablas y carga datos demo si la base está vacía (primer arranque).
    Base.metadata.create_all(bind=engine)
    from app.seed import seed_demo
    db = SessionLocal()
    try:
        seed_demo(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "API del sistema: CRM institucional + módulo de IA "
        "(scoring predictivo de conversión y clasificación NLP de mensajes). "
        "Docente: Poma Enrríquez, Genaro Raúl · Estudiante: Bayona Valdez, Fany"
    ),
    lifespan=lifespan,
)

app.include_router(auth_router.router)
app.include_router(contactos.router)
app.include_router(oportunidades.router)
app.include_router(tareas.router)
app.include_router(dashboard.router)
app.include_router(ml.router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/health", tags=["Infraestructura"])
def health():
    """Healthcheck para el despliegue (Render/Docker)."""
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(os.path.join("static", "index.html"))


@app.get("/app", include_in_schema=False)
def aplicacion():
    return FileResponse(os.path.join("static", "app.html"))
