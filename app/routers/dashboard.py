"""Dashboard: indicadores para la interfaz web (Chart.js)."""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Contacto, Oportunidad, Tarea, Usuario
from app.routers.tareas import alertas_seguimiento

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("")
def resumen(user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    total_contactos = db.query(func.count(Contacto.id)).scalar()
    por_tipo = (
        db.query(Contacto.tipo, func.count(Contacto.id))
        .group_by(Contacto.tipo)
        .all()
    )

    ops = db.query(Oportunidad).all()
    embudo = {"nuevo": 0, "contactado": 0, "negociacion": 0, "ganado": 0, "perdido": 0}
    for op in ops:
        embudo[op.etapa] = embudo.get(op.etapa, 0) + 1

    ganadas = embudo["ganado"]
    cerradas = ganadas + embudo["perdido"]
    tasa_conversion = round(ganadas / cerradas * 100, 1) if cerradas else 0.0

    monto_ganado = sum(o.monto_estimado for o in ops if o.etapa == "ganado")

    scores = [o.score_ia for o in ops if o.score_ia is not None]

    tareas_pendientes = (
        db.query(func.count(Tarea.id)).filter(Tarea.estado == "pendiente").scalar()
    )

    alertas = alertas_seguimiento(user=user, db=db)

    return {
        "total_contactos": total_contactos,
        "contactos_por_tipo": dict(por_tipo),
        "embudo": embudo,
        "tasa_conversion_pct": tasa_conversion,
        "monto_ganado_estimado": round(monto_ganado, 2),
        "oportunidades_con_score": len(scores),
        "score_promedio": round(sum(scores) / len(scores), 3) if scores else None,
        "tareas_pendientes": tareas_pendientes,
        "alertas_seguimiento": alertas["total"],
    }
