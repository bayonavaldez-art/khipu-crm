"""Conexión y sesión de base de datos (SQLAlchemy)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import get_settings

settings = get_settings()

# SQLite requiere este flag porque FastAPI usa varios hilos.
connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def get_db():
    """Dependencia de FastAPI: una sesión por request, cerrada al finalizar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
