"""Modelo de datos (ORM) — Khipu CRM Académico-Comercial.

Entidades: Usuario, Contacto, Interaccion, Oportunidad, Campana, Tarea.
Basado en el modelo de datos sugerido en la ficha del proyecto N.° 11.
"""
import datetime as dt

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean,
)
from sqlalchemy.orm import relationship

from app.database import Base


def ahora() -> dt.datetime:
    return dt.datetime.now()


class Usuario(Base):
    """Usuario interno del CRM con rol (RNF01: autenticación por roles)."""
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    full_name = Column(String(120), nullable=False)
    rol = Column(String(20), nullable=False)  # admin | gestor | admision | lector
    activo = Column(Boolean, default=True)
    creado = Column(DateTime, default=ahora)


class Contacto(Base):
    """Persona o institución: postulante, colegio, empresa, aliado, egresado."""
    __tablename__ = "contactos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    tipo = Column(String(20), nullable=False, index=True)      # postulante|colegio|empresa|aliado|egresado
    telefono = Column(String(30))
    correo = Column(String(120))
    canal_origen = Column(String(20))                           # whatsapp|web|correo|presencial
    procedencia = Column(String(150))                           # detalle libre (colegio, ciudad, etc.)
    estado = Column(String(20), default="activo")               # activo|inactivo
    notas = Column(Text)
    creado = Column(DateTime, default=ahora)

    interacciones = relationship("Interaccion", back_populates="contacto",
                                 cascade="all, delete-orphan")
    oportunidades = relationship("Oportunidad", back_populates="contacto",
                                 cascade="all, delete-orphan")
    tareas = relationship("Tarea", back_populates="contacto")


class Interaccion(Base):
    """Historial: llamadas, reuniones, mensajes, correos (RF01)."""
    __tablename__ = "interacciones"

    id = Column(Integer, primary_key=True, index=True)
    contacto_id = Column(Integer, ForeignKey("contactos.id"), nullable=False, index=True)
    tipo = Column(String(30), nullable=False)   # mensaje|llamada|reunion|correo|envio_informacion
    fecha = Column(DateTime, default=ahora)
    responsable = Column(String(120))
    comentario = Column(Text)
    # Horas que tardó el CRM en responder; alimenta el modelo de scoring (RF02).
    tiempo_respuesta_horas = Column(Float)

    contacto = relationship("Contacto", back_populates="interacciones")


class Oportunidad(Base):
    """Seguimiento comercial/académico con etapa de embudo y score de IA."""
    __tablename__ = "oportunidades"

    id = Column(Integer, primary_key=True, index=True)
    contacto_id = Column(Integer, ForeignKey("contactos.id"), nullable=False, index=True)
    titulo = Column(String(150), nullable=False)
    etapa = Column(String(20), nullable=False, default="nuevo", index=True)
    # nuevo|contactado|negociacion|ganado|perdido
    monto_estimado = Column(Float, default=0.0)
    estado = Column(String(20), default="abierta")             # abierta|ganada|perdida
    score_ia = Column(Float)                                   # probabilidad de conversión (ML)
    score_actualizado = Column(DateTime)
    creada = Column(DateTime, default=ahora)
    actualizada = Column(DateTime, default=ahora, onupdate=ahora)

    contacto = relationship("Contacto", back_populates="oportunidades")


class Campana(Base):
    """Agrupa contactos por evento, periodo o acción (admisión, convenios...)."""
    __tablename__ = "campanas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    fecha_inicio = Column(DateTime)
    fecha_fin = Column(DateTime)
    objetivo = Column(String(250))


class Tarea(Base):
    """Tareas de seguimiento y recordatorios (RF03)."""
    __tablename__ = "tareas"

    id = Column(Integer, primary_key=True, index=True)
    contacto_id = Column(Integer, ForeignKey("contactos.id"), index=True)
    titulo = Column(String(200), nullable=False)
    responsable = Column(String(120))
    fecha_limite = Column(DateTime)
    estado = Column(String(20), default="pendiente")           # pendiente|hecha
    creada = Column(DateTime, default=ahora)

    contacto = relationship("Contacto", back_populates="tareas")
