"""Pruebas unitarias del modelo de IA (scoring y NLP).

Validan que los artefactos entrenados cumplen umbrales mínimos de calidad
y que las predicciones se comportan de forma coherente con el negocio.
"""
import json
import os
import time

import pytest

from ml.service import ScoreRequest, clasificar_mensaje, predecir_score, recomendar_accion

ARTIFACTS = os.path.join("ml", "artifacts")


# ---------- Artefactos y métricas ----------
def test_artefactos_existen():
    assert os.path.exists(os.path.join(ARTIFACTS, "scoring_model.joblib"))
    assert os.path.exists(os.path.join(ARTIFACTS, "nlp_model.joblib"))


def test_metricas_scoring_superan_umbral():
    with open(os.path.join(ARTIFACTS, "scoring_metrics.json"), encoding="utf-8") as f:
        m = json.load(f)
    mejor = m["resultados"][m["modelo_seleccionado"]]
    assert mejor["accuracy"] >= 0.75, "Accuracy por debajo del umbral aceptable"
    assert mejor["f1"] >= 0.70
    assert mejor["roc_auc"] >= 0.80


def test_metricas_nlp_superan_umbral():
    with open(os.path.join(ARTIFACTS, "nlp_metrics.json"), encoding="utf-8") as f:
        m = json.load(f)
    assert m["accuracy"] >= 0.85
    assert m["f1_macro"] >= 0.85


# ---------- Coherencia de predicciones ----------
def _score(**kwargs):
    base = dict(
        tipo_contacto="postulante", canal_origen="whatsapp", etapa_embudo="nuevo",
        num_interacciones=1, tiempo_respuesta_promedio=48.0, dias_sin_interaccion=1.0,
    )
    base.update(kwargs)
    return predecir_score(ScoreRequest(**base))


def test_respuesta_rapida_convierte_mas_que_lenta():
    rapida = _score(tiempo_respuesta_promedio=2.0, num_interacciones=8,
                    etapa_embudo="negociacion")
    lenta = _score(tiempo_respuesta_promedio=200.0, num_interacciones=0,
                   etapa_embudo="nuevo")
    assert rapida > lenta


def test_probabilidades_en_rango_valido():
    assert 0.0 <= _score() <= 1.0
    assert 0.0 <= _score(etapa_embudo="ganado", num_interacciones=20) <= 1.0


def test_recomendaciones_coherentes():
    alta = recomendar_accion(0.9, 1)
    baja = recomendar_accion(0.1, 30)
    assert "entrevista" in alta.lower() or "cierre" in alta.lower()
    assert "reactivar" in baja.lower() or "perdido" in baja.lower()


def test_clasificacion_nlp_postulante():
    tipo, confianza = clasificar_mensaje(
        "Hola, quiero información sobre la carrera de computación para postular")
    assert tipo == "postulante"
    assert confianza > 0.5


def test_clasificacion_nlp_empresa():
    tipo, _ = clasificar_mensaje(
        "Somos una empresa minera y queremos un convenio para practicantes")
    assert tipo == "empresa"


def test_clasificacion_nlp_colegio():
    tipo, _ = clasificar_mensaje(
        "Buenos días, somos del colegio Salesianos y deseamos coordinar una visita")
    assert tipo == "colegio"


def test_clasificacion_nlp_egresado():
    tipo, _ = clasificar_mensaje(
        "Soy egresado de la promoción 2019 y necesito mis certificados")
    assert tipo == "egresado"


# ---------- Rendimiento (RNF02: score < 3 s) ----------
def test_rendimiento_scoring():
    inicio = time.time()
    for _ in range(100):
        _score()
    duracion = time.time() - inicio
    assert duracion < 3.0, f"100 scores tardaron {duracion:.2f} s (>3 s)"
