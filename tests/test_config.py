"""Pruebas de la configuración: normalización de URLs de PostgreSQL.

Render entrega la conexión como "postgres://..." y docker-compose como
"postgresql+psycopg://...": ambas deben terminar normalizadas al esquema
que SQLAlchemy 2 espera con el driver psycopg 3.
"""
import importlib
import os

import app.config as config


def _url_normalizada(url: str) -> str:
    """Fija DATABASE_URL=url, recarga la configuración y devuelve la URL
    efectiva; restaura el entorno al terminar."""
    previo = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    try:
        config.get_settings.cache_clear()
        importlib.reload(config)
        return config.get_settings().DATABASE_URL
    finally:
        if previo is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previo
        config.get_settings.cache_clear()
        importlib.reload(config)


def test_url_render_postgres_esquema_doble():
    resultado = _url_normalizada("postgres://usuario:clave@host:5432/khipu_crm")
    assert resultado.startswith("postgresql+psycopg://usuario:clave@host")


def test_url_sqlalchemy_ya_normalizada():
    resultado = _url_normalizada("postgresql://usuario:clave@host:5432/khipu_crm")
    assert resultado.startswith("postgresql+psycopg://usuario:clave@host")


def test_url_sqlite_intacta():
    resultado = _url_normalizada("sqlite:///./test.db")
    assert resultado == "sqlite:///./test.db"
