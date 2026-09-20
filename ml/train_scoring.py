"""Entrena y evalúa el modelo de Scoring Predictivo (RF02).

Pipeline (scikit-learn):
  1. Limpieza: duplicados eliminados; outliers de tiempo de respuesta (>720 h)
     tratados como nulos; nulos imputados con la mediana.
  2. Codificación: one-hot para categóricas; estandarización para numéricas.
  3. Comparación de LogisticRegression vs RandomForest; se conserva el mejor
     según F1 (clase positiva) y ROC-AUC.
  4. Métricas guardadas en JSON para el informe (rúbrica: "evaluado con
     métricas y resultados justificados").

Uso:  python -m ml.train_scoring
Salida: ml/artifacts/scoring_model.joblib + scoring_metrics.json
"""
import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, confusion_matrix, f1_score, precision_score,
    recall_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SEED = 42
LIMITE_OUTLIER_HORAS = 720  # > 30 días de "respuesta" = dato irrecuperable

CAT_FEATURES = ["tipo_contacto", "canal_origen", "etapa_embudo"]
NUM_FEATURES = ["num_interacciones", "tiempo_respuesta_promedio", "dias_sin_interaccion"]
TARGET = "convertido"


def cargar_y_limpiar(ruta_csv: str) -> pd.DataFrame:
    df = pd.read_csv(ruta_csv)

    # 1) Duplicados exactos (herencia de hojas de cálculo).
    antes = len(df)
    df = df.drop_duplicates(subset=["id_contacto"]).reset_index(drop=True)
    print(f"Limpieza - duplicados eliminados: {antes - len(df)}")

    # 2) Outliers: tiempos de respuesta imposibles se tratan como nulos.
    outliers = df["tiempo_respuesta_promedio"] > LIMITE_OUTLIER_HORAS
    print(f"Limpieza - outliers convertidos a nulo: {outliers.sum()}")
    df.loc[outliers, "tiempo_respuesta_promedio"] = np.nan

    # 3) Nulos: imputación con mediana (los imputer del pipeline la aprenden).
    print(f"Limpieza - nulos a imputar: {df['tiempo_respuesta_promedio'].isna().sum()}")
    return df


def construir_preprocesador() -> ColumnTransformer:
    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer([
        ("num", num_pipeline, NUM_FEATURES),
        ("cat", cat_pipeline, CAT_FEATURES),
    ])


def evaluar(modelo, X_test, y_test) -> dict:
    y_pred = modelo.predict(X_test)
    y_prob = modelo.predict_proba(X_test)[:, 1]
    return {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
        "matriz_confusion": confusion_matrix(y_test, y_pred).tolist(),
    }


def main():
    artifacts = os.path.join("ml", "artifacts")
    os.makedirs(artifacts, exist_ok=True)

    df = cargar_y_limpiar(os.path.join("ml", "data", "dataset_scoring.csv"))
    X = df[CAT_FEATURES + NUM_FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=SEED
    )

    candidatos = {
        "LogisticRegression": Pipeline([
            ("prep", construir_preprocesador()),
            ("clf", LogisticRegression(max_iter=1000, random_state=SEED)),
        ]),
        "RandomForest": Pipeline([
            ("prep", construir_preprocesador()),
            ("clf", RandomForestClassifier(n_estimators=300, random_state=SEED, n_jobs=-1)),
        ]),
    }

    resultados = {}
    for nombre, pipeline in candidatos.items():
        pipeline.fit(X_train, y_train)
        resultados[nombre] = evaluar(pipeline, X_test, y_test)
        m = resultados[nombre]
        print(f"{nombre}: acc={m['accuracy']} f1={m['f1']} auc={m['roc_auc']}")

    # Selección por F1, desempate por ROC-AUC.
    mejor_nombre = max(resultados, key=lambda n: (resultados[n]["f1"], resultados[n]["roc_auc"]))
    mejor = candidatos[mejor_nombre]
    print(f"Modelo seleccionado: {mejor_nombre}")

    joblib.dump(mejor, os.path.join(artifacts, "scoring_model.joblib"))

    informe = {
        "modelo_seleccionado": mejor_nombre,
        "filas_dataset": int(len(df)),
        "distribucion_target": {"convertido_1": int(y.sum()), "convertido_0": int(len(y) - y.sum())},
        "features_categoricas": CAT_FEATURES,
        "features_numericas": NUM_FEATURES,
        "limite_outlier_horas": LIMITE_OUTLIER_HORAS,
        "resultados": resultados,
        "modelo": {n: resultados[n] for n in resultados},
    }
    with open(os.path.join(artifacts, "scoring_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(informe, f, ensure_ascii=False, indent=2)
    print(f"Artefactos guardados en {artifacts}/")


if __name__ == "__main__":
    main()
