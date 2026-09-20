"""CRUD de contactos e historial de interacciones (RF01)."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_rol
from app.database import get_db
from app.models import Contacto, Interaccion, Usuario
from app.schemas import ContactoIn, ContactoOut, ContactoUpdate, InteraccionIn, InteraccionOut

router = APIRouter(prefix="/contactos", tags=["Contactos"])


@router.get("", response_model=list[ContactoOut])
def listar_contactos(
    q: Optional[str] = Query(None, max_length=100, description="Búsqueda por nombre/correo"),
    tipo: Optional[str] = Query(None, pattern="^(postulante|colegio|empresa|aliado|egresado)$"),
    estado: Optional[str] = Query(None, pattern="^(activo|inactivo)$"),
    limite: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    consulta = db.query(Contacto)
    if q:
        filtro = f"%{q.lower()}%"
        consulta = consulta.filter(
            (Contacto.nombre.ilike(f"%{q}%")) | (Contacto.correo.ilike(f"%{q}%"))
        )
    if tipo:
        consulta = consulta.filter(Contacto.tipo == tipo)
    if estado:
        consulta = consulta.filter(Contacto.estado == estado)
    return (
        consulta.order_by(Contacto.id.desc())
        .offset(offset)
        .limit(limite)
        .all()
    )


@router.post("", response_model=ContactoOut, status_code=status.HTTP_201_CREATED)
def crear_contacto(
    datos: ContactoIn,
    user: Usuario = Depends(require_rol("admision")),
    db: Session = Depends(get_db),
):
    contacto = Contacto(**datos.model_dump())
    db.add(contacto)
    db.commit()
    db.refresh(contacto)
    return contacto


@router.get("/{contacto_id}", response_model=ContactoOut)
def obtener_contacto(
    contacto_id: int,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contacto = db.get(Contacto, contacto_id)
    if contacto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contacto no encontrado")
    return contacto


@router.put("/{contacto_id}", response_model=ContactoOut)
def actualizar_contacto(
    contacto_id: int,
    datos: ContactoUpdate,
    user: Usuario = Depends(require_rol("admision")),
    db: Session = Depends(get_db),
):
    contacto = db.get(Contacto, contacto_id)
    if contacto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contacto no encontrado")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(contacto, campo, valor)
    db.commit()
    db.refresh(contacto)
    return contacto


@router.delete("/{contacto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_contacto(
    contacto_id: int,
    user: Usuario = Depends(require_rol("admin")),
    db: Session = Depends(get_db),
):
    contacto = db.get(Contacto, contacto_id)
    if contacto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contacto no encontrado")
    db.delete(contacto)
    db.commit()


# ---------- Interacciones ----------
@router.get("/{contacto_id}/interacciones", response_model=list[InteraccionOut])
def listar_interacciones(
    contacto_id: int,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contacto = db.get(Contacto, contacto_id)
    if contacto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contacto no encontrado")
    return (
        db.query(Interaccion)
        .filter(Interaccion.contacto_id == contacto_id)
        .order_by(Interaccion.fecha.desc())
        .all()
    )


@router.post(
    "/{contacto_id}/interacciones",
    response_model=InteraccionOut,
    status_code=status.HTTP_201_CREATED,
)
def registrar_interaccion(
    contacto_id: int,
    datos: InteraccionIn,
    user: Usuario = Depends(require_rol("admision")),
    db: Session = Depends(get_db),
):
    contacto = db.get(Contacto, contacto_id)
    if contacto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Contacto no encontrado")
    interaccion = Interaccion(
        contacto_id=contacto_id,
        tipo=datos.tipo,
        comentario=datos.comentario,
        tiempo_respuesta_horas=datos.tiempo_respuesta_horas,
        responsable=user.full_name,
    )
    db.add(interaccion)
    db.commit()
    db.refresh(interaccion)
    return interaccion
