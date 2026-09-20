"""Tareas, recordatorios, campañas y alertas de seguimiento (RF03)."""
import datetime as dt
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_rol
from app.config import get_settings
from app.database import get_db
from app.models import Campana, Contacto, Interaccion, Oportunidad, Tarea, Usuario
from app.schemas import CampanaIn, CampanaOut, TareaIn, TareaOut

settings = get_settings()

router = APIRouter(tags=["Tareas y campañas"])


# ---------- Tareas ----------
@router.get("/tareas", response_model=list[TareaOut])
def listar_tareas(
    estado: Optional[str] = Query(None, pattern="^(pendiente|hecha)$"),
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    consulta = db.query(Tarea)
    if estado:
        consulta = consulta.filter(Tarea.estado == estado)
    return consulta.order_by(Tarea.fecha_limite.asc().nullslast()).all()


@router.post("/tareas", response_model=TareaOut, status_code=status.HTTP_201_CREATED)
def crear_tarea(
    datos: TareaIn,
    user: Usuario = Depends(require_rol("admision")),
    db: Session = Depends(get_db),
):
    valores = datos.model_dump(exclude={"responsable"})
    tarea = Tarea(**valores, responsable=datos.responsable or user.full_name)
    db.add(tarea)
    db.commit()
    db.refresh(tarea)
    return tarea


@router.put("/tareas/{tarea_id}/completar", response_model=TareaOut)
def completar_tarea(
    tarea_id: int,
    user: Usuario = Depends(require_rol("admision")),
    db: Session = Depends(get_db),
):
    tarea = db.get(Tarea, tarea_id)
    if tarea is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarea no encontrada")
    tarea.estado = "hecha"
    db.commit()
    db.refresh(tarea)
    return tarea


# ---------- Campañas ----------
@router.get("/campanas", response_model=list[CampanaOut])
def listar_campanas(
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Campana).order_by(Campana.id.desc()).all()


@router.post("/campanas", response_model=CampanaOut, status_code=status.HTTP_201_CREATED)
def crear_campana(
    datos: CampanaIn,
    user: Usuario = Depends(require_rol("admision")),
    db: Session = Depends(get_db),
):
    campana = Campana(**datos.model_dump())
    db.add(campana)
    db.commit()
    db.refresh(campana)
    return campana


# ---------- Alertas (RF03) ----------
@router.get("/alertas")
def alertas_seguimiento(
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Oportunidades abiertas cuyo contacto lleva más de N días sin interacción."""
    limite_dias = settings.ALERTA_DIAS_SIN_INTERACCION
    ahora = dt.datetime.now()
    resultado = []

    ops = (
        db.query(Oportunidad)
        .filter(Oportunidad.estado == "abierta")
        .all()
    )
    for op in ops:
        ultima = (
            db.query(Interaccion.fecha)
            .filter(Interaccion.contacto_id == op.contacto_id)
            .order_by(Interaccion.fecha.desc())
            .first()
        )
        if ultima is None:
            dias = 999  # nunca contactado
            ultima_fecha = None
        else:
            ultima_fecha = ultima[0]
            dias = (ahora - ultima_fecha).total_seconds() / 86400

        if dias >= limite_dias:
            contacto = op.contacto
            resultado.append({
                "oportunidad_id": op.id,
                "titulo": op.titulo,
                "contacto": contacto.nombre,
                "etapa": op.etapa,
                "dias_sin_interaccion": round(dias, 1),
                "ultima_interaccion": ultima_fecha,
                "mensaje": (
                    "Sin interacción registrada: priorizar contacto"
                    if ultima_fecha is None
                    else f"Sin interacción hace {dias:.0f} días: priorizar contacto"
                ),
            })

    resultado.sort(key=lambda a: -a["dias_sin_interaccion"])
    return {"dias_limite": limite_dias, "total": len(resultado), "alertas": resultado}
