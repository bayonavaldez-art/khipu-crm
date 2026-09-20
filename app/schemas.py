"""Esquemas de validación de entrada/salida (Pydantic).

La validación estricta de inputs es parte del checklist de seguridad.
"""
import datetime as dt
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, EmailStr, Field

TIPOS_CONTACTO = ["postulante", "colegio", "empresa", "aliado", "egresado"]
CANALES = ["whatsapp", "web", "correo", "presencial"]
ETAPAS = ["nuevo", "contactado", "negociacion", "ganado", "perdido"]
ROLES = ["admin", "gestor", "admision", "lector"]


# ---------- Auth ----------
class LoginIn(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: str
    full_name: str


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    full_name: str
    rol: str


# ---------- Contactos ----------
class ContactoIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    tipo: str = Field(pattern="^(postulante|colegio|empresa|aliado|egresado)$")
    telefono: Optional[str] = Field(None, max_length=30)
    correo: Optional[EmailStr] = None
    canal_origen: Optional[str] = Field(None, pattern="^(whatsapp|web|correo|presencial)$")
    procedencia: Optional[str] = Field(None, max_length=150)
    notas: Optional[str] = None


class ContactoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=150)
    tipo: Optional[str] = Field(None, pattern="^(postulante|colegio|empresa|aliado|egresado)$")
    telefono: Optional[str] = Field(None, max_length=30)
    correo: Optional[EmailStr] = None
    canal_origen: Optional[str] = Field(None, pattern="^(whatsapp|web|correo|presencial)$")
    procedencia: Optional[str] = Field(None, max_length=150)
    estado: Optional[str] = Field(None, pattern="^(activo|inactivo)$")
    notas: Optional[str] = None


class ContactoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    tipo: str
    telefono: Optional[str]
    correo: Optional[str]
    canal_origen: Optional[str]
    procedencia: Optional[str]
    estado: str
    notas: Optional[str]
    creado: dt.datetime


# ---------- Interacciones ----------
class InteraccionIn(BaseModel):
    tipo: str = Field(pattern="^(mensaje|llamada|reunion|correo|envio_informacion)$")
    comentario: Optional[str] = None
    tiempo_respuesta_horas: Optional[float] = Field(None, ge=0, le=24 * 365)


class InteraccionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    contacto_id: int
    tipo: str
    fecha: dt.datetime
    responsable: Optional[str]
    comentario: Optional[str]
    tiempo_respuesta_horas: Optional[float]


# ---------- Oportunidades ----------
class OportunidadIn(BaseModel):
    contacto_id: int
    titulo: str = Field(min_length=3, max_length=150)
    etapa: str = Field("nuevo", pattern="^(nuevo|contactado|negociacion|ganado|perdido)$")
    monto_estimado: float = Field(0, ge=0)


class OportunidadUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=3, max_length=150)
    etapa: Optional[str] = Field(None, pattern="^(nuevo|contactado|negociacion|ganado|perdido)$")
    monto_estimado: Optional[float] = Field(None, ge=0)
    estado: Optional[str] = Field(None, pattern="^(abierta|ganada|perdida)$")


class OportunidadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    contacto_id: int
    titulo: str
    etapa: str
    monto_estimado: float
    estado: str
    score_ia: Optional[float]
    score_actualizado: Optional[dt.datetime]
    creada: dt.datetime
    contacto_nombre: Optional[str] = None


# ---------- Campañas ----------
class CampanaIn(BaseModel):
    nombre: str = Field(min_length=3, max_length=150)
    fecha_inicio: Optional[dt.datetime] = None
    fecha_fin: Optional[dt.datetime] = None
    objetivo: Optional[str] = Field(None, max_length=250)


class CampanaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    fecha_inicio: Optional[dt.datetime]
    fecha_fin: Optional[dt.datetime]
    objetivo: Optional[str]


# ---------- Tareas ----------
class TareaIn(BaseModel):
    contacto_id: Optional[int] = None
    titulo: str = Field(min_length=3, max_length=200)
    responsable: Optional[str] = Field(None, max_length=120)
    fecha_limite: Optional[dt.datetime] = None


class TareaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    contacto_id: Optional[int]
    titulo: str
    responsable: Optional[str]
    fecha_limite: Optional[dt.datetime]
    estado: str
    creada: dt.datetime


# ---------- IA ----------
class ScoreIn(BaseModel):
    """Entrada directa para el scoring (si no se envia oportunidad_id)."""
    tipo_contacto: str = Field(pattern="^(postulante|colegio|empresa|aliado|egresado)$")
    canal_origen: str = Field(pattern="^(whatsapp|web|correo|presencial)$")
    etapa_embudo: str = Field(pattern="^(nuevo|contactado|negociacion|ganado|perdido)$")
    num_interacciones: int = Field(ge=0, le=500)
    tiempo_respuesta_promedio: float = Field(ge=0, le=24 * 365)
    dias_sin_interaccion: float = Field(ge=0, le=3650)


class ScoreOut(BaseModel):
    probabilidad_conversion: float
    recomendacion: str
    variables_usadas: dict


class ClassifyIn(BaseModel):
    mensaje: str = Field(min_length=5, max_length=1000)
    crear_contacto: bool = False
    nombre_contacto: Optional[str] = Field(None, min_length=2, max_length=150)


class ClassifyOut(BaseModel):
    tipo_contacto: str
    confianza: float
    contacto_id: Optional[int] = None
