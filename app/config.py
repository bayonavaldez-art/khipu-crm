"""Configuración central del sistema.

Toda credencial o parámetro sensible se lee desde variables de entorno
(ver .env.example). Nunca se hardcoden secretos en el código fuente.
"""
import os
from functools import lru_cache


class Settings:
    APP_NAME = "Khipu CRM Académico-Comercial"
    APP_VERSION = "1.0.0"

    # Secretos: en producción SIEMPRE definirlos como variables de entorno.
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-cambiar-en-produccion")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

    # Base de datos: SQLite por defecto (desarrollo), PostgreSQL en despliegue.
    _db_url = os.getenv("DATABASE_URL", "sqlite:///./khipu_crm.db")
    # Render entrega "postgres://..." y SQLAlchemy 2 usa el driver psycopg (v3):
    # ambos prefijos se normalizan antes de crear el engine.
    if _db_url.startswith(("postgresql://", "postgres://")):
        _db_url = _db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        _db_url = _db_url.replace("postgres://", "postgresql+psycopg://", 1)
    DATABASE_URL = _db_url

    # Ruta de los artefactos de IA entrenados (pipeline de scoring y NLP).
    ML_ARTIFACTS_DIR = os.getenv("ML_ARTIFACTS_DIR", os.path.join("ml", "artifacts"))

    # Días sin interacción para disparar alertas de seguimiento (RF03).
    ALERTA_DIAS_SIN_INTERACCION = int(os.getenv("ALERTA_DIAS_SIN_INTERACCION", "7"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
