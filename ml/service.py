"""Servicio de inferencia: carga los artefactos de IA y expone predicciones.

El modelo se carga una sola vez (lazy singleton) para cumplir el RNF02
(score en < 3 s incluso con 10 000 contactos).
"""
import os
from functools import lru_cache

import joblib
import pandas as pd
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()


class ScoreRequest(BaseModel):
    tipo_contacto: str
    canal_origen: str
    etapa_embudo: str
    num_interacciones: int
    tiempo_respuesta_promedio: float
    dias_sin_interaccion: float


@lru_cache
def _cargar_scoring():
    ruta = os.path.join(settings.ML_ARTIFACTS_DIR, "scoring_model.joblib")
    if not os.path.exists(ruta):
        raise RuntimeError(
            "Modelo de scoring no encontrado. Ejecutar: python -m ml.train_scoring"
        )
    return joblib.load(ruta)


@lru_cache
def _cargar_nlp():
    ruta = os.path.join(settings.ML_ARTIFACTS_DIR, "nlp_model.joblib")
    if not os.path.exists(ruta):
        raise RuntimeError(
            "Modelo NLP no encontrado. Ejecutar: python -m ml.train_nlp"
        )
    return joblib.load(ruta)


def predecir_score(req: ScoreRequest) -> float:
    """Devuelve la probabilidad de conversión (0-1) para una oportunidad."""
    modelo = _cargar_scoring()
    entrada = pd.DataFrame([req.model_dump()])
    return float(modelo.predict_proba(entrada)[0, 1])


def clasificar_mensaje(mensaje: str):
    """Devuelve (tipo_contacto, confianza) para un mensaje entrante."""
    modelo = _cargar_nlp()
    tipo = str(modelo.predict([mensaje])[0])
    confianza = float(modelo.predict_proba([mensaje]).max())
    return tipo, confianza


def recomendar_accion(probabilidad: float, dias_sin_interaccion: float) -> str:
    """Módulo de recomendación: próxima acción sugerida según score y
    urgencia. Heurística derivada de los patrones del histórico (los contactos
    exitosos se caracterizan por respuestas rápidas y seguimiento frecuente)."""
    if dias_sin_interaccion >= 7:
        if probabilidad >= 0.5:
            return ("URGENTE: contacto de alto valor sin interacción hace "
                    f"{dias_sin_interaccion:.0f} días. Llamar hoy y agendar entrevista.")
        return (f"Sin interacción hace {dias_sin_interaccion:.0f} días y baja probabilidad "
                "de conversión. Reactivar con campaña o evaluar cerrar como perdido.")
    if probabilidad >= 0.7:
        return "Alta probabilidad de conversión: agendar entrevista de cierre hoy."
    if probabilidad >= 0.4:
        return "Probabilidad media: llamar hoy y enviar información específica."
    return "Probabilidad baja: enviar información y programar seguimiento en una semana."
