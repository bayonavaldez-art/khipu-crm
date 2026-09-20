"""CRUD de oportunidades (embudo comercial/académico)."""
import datetime as dt
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_rol
from app.database import get_db
from app.models import Contacto, Oportunidad, Usuario
from app.schemas import OportunidadIn, OportunidadOut, OportunidadUpdate
from ml.service import ScoreRequest, predecir_score, recomendar_accion

router = APIRouter(prefix="/oportunidades", tags=["Oportunidades"])


def _a_out(o: Oportunidad) -> OportunidadOut:
    out = OportunidadOut.model_validate(o)
    out.contacto_nombre = o.contacto.nombre if o.contacto else None
    return out


@router.get("", response_model=list[OportunidadOut])
def listar_oportunidades(
    etapa: Optional[str] = Query(None, pattern="^(nuevo|contactado|negociacion|ganado|perdido)$"),
    contacto_id: Optional[int] = None,
    limite: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    consulta = db.query(Oportunidad)
    if etapa:
        consulta = consulta.filter(Oportunidad.etapa == etapa)
    if contacto_id:
        consulta = consulta.filter(Oportunidad.contacto_id == contacto_id)
    return consulta.order_by(Oportunidad.id.desc()).offset(offset).limit(limite).all()


@router.post("", response_model=OportunidadOut, status_code=status.HTTP_201_CREATED)
def crear_oportunidad(
    datos: OportunidadIn,
    user: Usuario = Depends(require_rol("admision")),
    db: Session = Depends(get_db),
):
    contacto = db.get(Contacto, datos.contacto_id)
    if contacto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El contacto indicado no existe")
    op = Oportunidad(**datos.model_dump())
    db.add(op)
    db.commit()
    db.refresh(op)
    return _a_out(op)


@router.put("/{op_id}", response_model=OportunidadOut)
def actualizar_oportunidad(
    op_id: int,
    datos: OportunidadUpdate,
    user: Usuario = Depends(require_rol("admision")),
    db: Session = Depends(get_db),
):
    op = db.get(Oportunidad, op_id)
    if op is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Oportunidad no encontrada")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(op, campo, valor)
    db.commit()
    db.refresh(op)
    return _a_out(op)


@router.post("/{op_id}/score")
def calcular_score(
    op_id: int,
    user: Usuario = Depends(require_rol("admision")),
    db: Session = Depends(get_db),
):
    """Calcula con el modelo de ML la probabilidad de conversión de la
    oportunidad, usando las interacciones reales registradas, y la persiste."""
    op = db.get(Oportunidad, op_id)
    if op is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Oportunidad no encontrada")

    contacto = op.contacto
    interacciones = contacto.interacciones

    tiempos = [i.tiempo_respuesta_horas for i in interacciones if i.tiempo_respuesta_horas is not None]
    promedio_respuesta = sum(tiempos) / len(tiempos) if tiempos else 48.0

    if interacciones:
        ultima = max(i.fecha for i in interacciones)
        dias_sin = (dt.datetime.now() - ultima).total_seconds() / 86400
    else:
        dias_sin = 30.0

    req = ScoreRequest(
        tipo_contacto=contacto.tipo,
        canal_origen=contacto.canal_origen or "web",
        etapa_embudo=op.etapa,
        num_interacciones=len(interacciones),
        tiempo_respuesta_promedio=promedio_respuesta,
        dias_sin_interaccion=dias_sin,
    )
    prob = predecir_score(req)
    recomendacion = recomendar_accion(prob, dias_sin)

    op.score_ia = round(prob, 4)
    op.score_actualizado = dt.datetime.now()
    db.commit()

    return {
        "oportunidad_id": op.id,
        "probabilidad_conversion": round(prob, 4),
        "recomendacion": recomendacion,
        "variables_usadas": req.model_dump(),
    }
