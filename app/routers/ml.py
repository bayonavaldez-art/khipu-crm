"""Endpoints del módulo de IA: scoring predictivo y clasificación NLP."""
import json
import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_rol
from app.config import get_settings
from app.database import get_db
from ml.service import (
    ScoreRequest, clasificar_mensaje, predecir_score, recomendar_accion,
)
from app.models import Contacto, Usuario
from app.schemas import ClassifyIn, ClassifyOut, ScoreIn, ScoreOut

settings = get_settings()
router = APIRouter(prefix="/ml", tags=["Inteligencia Artificial"])


@router.post("/score", response_model=ScoreOut)
def score_entrada(
    datos: ScoreIn,
    user: Usuario = Depends(get_current_user),
):
    """Calcula la probabilidad de conversión para variables dadas
    (usado por el dashboard y pruebas del modelo)."""
    req = ScoreRequest(**datos.model_dump())
    prob = predecir_score(req)
    return ScoreOut(
        probabilidad_conversion=round(prob, 4),
        recomendacion=recomendar_accion(prob, datos.dias_sin_interaccion),
        variables_usadas=req.model_dump(),
    )


@router.post("/classify", response_model=ClassifyOut)
def classify(
    datos: ClassifyIn,
    user: Usuario = Depends(require_rol("admision")),
    db: Session = Depends(get_db),
):
    """KhipuBot: clasifica un mensaje entrante por tipo de contacto (NLP) y,
    opcionalmente, crea el contacto automáticamente (RF01)."""
    tipo, confianza = clasificar_mensaje(datos.mensaje)

    contacto_id = None
    if datos.crear_contacto:
        contacto = Contacto(
            nombre=datos.nombre_contacto or f"Contacto KhipuBot ({tipo})",
            tipo=tipo,
            canal_origen="whatsapp",
            notas=f" creado automáticamente desde mensaje: {datos.mensaje[:200]}",
        )
        db.add(contacto)
        db.commit()
        db.refresh(contacto)
        contacto_id = contacto.id

    return ClassifyOut(tipo_contacto=tipo, confianza=round(confianza, 4), contacto_id=contacto_id)


@router.get("/model-info")
def model_info(user: Usuario = Depends(get_current_user)):
    """Métricas de evaluación de ambos modelos (evidencia para el informe)."""
    resultado = {}
    for nombre, archivo in [("scoring", "scoring_metrics.json"), ("nlp", "nlp_metrics.json")]:
        ruta = os.path.join(settings.ML_ARTIFACTS_DIR, archivo)
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8") as f:
                resultado[nombre] = json.load(f)
        else:
            resultado[nombre] = {"error": "métricas no generadas"}
    if not resultado:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Modelos no entrenados")
    return resultado
