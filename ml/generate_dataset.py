"""Genera el dataset sintético de entrenamiento del modelo de scoring (RF02).

Simula el histórico centralizado de contactos e interacciones que hoy Khipu
tiene disperso en hojas de cálculo, WhatsApp y correos. Incluye de forma
intencional: valores nulos (~5%), outliers (tiempos de respuesta absurdos) y
registros duplicados, para ejercitar las tareas de preparación de datos
descritas en el documento de arquitectura (limpieza, imputación, codificación).

Uso:  python -m ml.generate_dataset
Salida: ml/data/dataset_scoring.csv
"""
import os

import numpy as np
import pandas as pd

SEED = 42
N = 4000

TIPOS = ["postulante", "colegio", "empresa", "aliado", "egresado"]
CANALES = ["whatsapp", "web", "correo", "presencial"]
ETAPAS = ["nuevo", "contactado", "negociacion", "ganado", "perdido"]


def main():
    rng = np.random.default_rng(SEED)

    tipos = rng.choice(TIPOS, N, p=[0.45, 0.15, 0.15, 0.15, 0.10])
    canales = rng.choice(CANALES, N, p=[0.40, 0.25, 0.20, 0.15])

    num_interacciones = rng.poisson(lam=4, size=N)
    # Tiempo de respuesta en horas: exponencial (rápido es mejor).
    tiempo_respuesta = rng.exponential(scale=36, size=N)
    dias_sin_interaccion = rng.gamma(shape=2, scale=5, size=N)

    # ---- Etapa del embudo: correlacionada con el comportamiento ----
    # A más interacciones y menos días sin contacto, más avanzada la etapa.
    progreso = (
        num_interacciones * 0.8
        - np.log1p(tiempo_respuesta)
        - dias_sin_interaccion * 0.6
        + rng.normal(0, 2.5, N)
    )
    umbral = np.quantile(progreso, [0.25, 0.55, 0.80])
    etapa = np.where(progreso < umbral[0], "nuevo",
             np.where(progreso < umbral[1], "contactado",
             np.where(progreso < umbral[2], "negociacion", "ganado")))
    # Una fracción de las oportunidades se pierde en cualquier etapa.
    perdidas = rng.random(N) < 0.15
    etapa = np.where(perdidas, "perdido", etapa)
    etapa = etapa.astype(object)

    # ---- Variable objetivo: convertido (1/0) ----
    # Los ganados convierten; entre los demás, la probabilidad depende del
    # comportamiento (más interacciones, respuestas rápidas → más conversión).
    etapa_num = np.select(
        [etapa == "nuevo", etapa == "contactado", etapa == "negociacion", etapa == "ganado"],
        [0, 1, 2, 3], default=0,
    )
    logito = (
        -1.2
        + 1.4 * etapa_num
        + 0.25 * num_interacciones
        - 0.035 * tiempo_respuesta
        - 0.10 * dias_sin_interaccion
        + np.where(canales == "whatsapp", 0.35, 0.0)
        + np.where(canales == "presencial", 0.25, 0.0)
        + np.where(tipos == "postulante", 0.30, np.where(tipos == "empresa", 0.15, 0.0))
        + rng.normal(0, 0.8, N)
    )
    prob = 1 / (1 + np.exp(-logito))
    convertido = (rng.random(N) < prob).astype(int)

    df = pd.DataFrame({
        "id_contacto": np.arange(1, N + 1),
        "tipo_contacto": tipos,
        "canal_origen": canales,
        "etapa_embudo": etapa,
        "num_interacciones": num_interacciones.astype(float),
        "tiempo_respuesta_promedio": tiempo_respuesta.round(2),
        "dias_sin_interaccion": dias_sin_interaccion.round(2),
        "convertido": convertido,
    })

    # ---- Suciedad intencional para ejercitar la limpieza ----
    # 5% de nulos en tiempo de respuesta.
    nulos = rng.random(N) < 0.05
    df.loc[nulos, "tiempo_respuesta_promedio"] = np.nan

    # ~1% de outliers: contactos abandonados con meses de "respuesta".
    outliers = rng.random(N) < 0.01
    df.loc[outliers, "tiempo_respuesta_promedio"] = rng.uniform(4000, 9000, outliers.sum()).round(2)

    # ~0.5% de filas duplicadas (herencia de hojas de cálculo).
    dups = df.sample(n=int(N * 0.005), random_state=SEED)
    df = pd.concat([df, dups], ignore_index=True)

    os.makedirs("ml/data", exist_ok=True)
    ruta = os.path.join("ml", "data", "dataset_scoring.csv")
    df.to_csv(ruta, index=False)
    print(f"Dataset generado: {ruta} ({len(df)} filas)")
    print(f"  Tasa de conversión global: {df['convertido'].mean():.2%}")
    print(f"  Nulos en tiempo_respuesta: {df['tiempo_respuesta_promedio'].isna().sum()}")


if __name__ == "__main__":
    main()
