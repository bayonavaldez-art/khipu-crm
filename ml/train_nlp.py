"""Entrena el clasificador NLP de KhipuBot (RF01).

Clasifica mensajes entrantes (WhatsApp/web/correo) en el tipo de contacto:
postulante, colegio, empresa, aliado o egresado. Usa TF-IDF sobre n-gramas
(1-2) + LogisticRegression: ligero, sin dependencias pesadas y suficiente
para el volumen del proyecto.

Uso:  python -m ml.train_nlp
Salida: ml/artifacts/nlp_model.joblib + nlp_metrics.json
"""
import json
import os
import random

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

SEED = 42
random.seed(SEED)

# Plantillas por clase; se combinan con aperturas/cierres para simular la
# variabilidad real de mensajes que recibe Khipu.
PLANTILLAS = {
    "postulante": [
        "Hola, quiero información sobre la carrera de {carrera}",
        "Quisiera postular al instituto, ¿cuáles son los requisitos?",
        "Buenas tardes, ¿cuándo inician las inscripciones para {carrera}?",
        "Soy interesado en estudiar {carrera}, necesito saber los costos",
        "¿Hay becas o descuentos para nuevos alumnos en {carrera}?",
        "Quiero saber el pensum de {carrera} y la duración",
        "Hola, soy egresado del colegio y quiero seguir estudiando {carrera}",
        "Necesito información de admisión para el próximo semestre",
        "¿Puedo inscribirme en {carrera} si aún estoy en quinto de secundaria?",
        "Quiero matricularme en {carrera}, ¿a dónde debo ir?",
    ],
    "colegio": [
        "Somos del colegio {colegio}, queremos coordinar una visita institucional",
        "Buenos días, represento al colegio {colegio} y deseo agendar una charla",
        "Soy director del colegio {colegio}, nos interesa un convenio educativo",
        "El colegio {colegio} solicita información sobre talleres para alumnos",
        "Queremos llevar a nuestros estudiantes de {colegio} a conocer el instituto",
        "Coordinadora académica de {colegio}, necesitamos presupuestos para feria",
        "Desde el colegio {colegio} consultamos por carreras técnicas para egresados",
        "Hola, somos profesores de {colegio} y queremos una visita guiada",
    ],
    "empresa": [
        "Somos una empresa interesada en un convenio con el instituto",
        "Buenos días, nuestra compañía busca practicantes de {carrera}",
        "Represento a una empresa y queremos proponer un convenio marco",
        "Necesitamos contratar técnicos en {carrera}, ¿cómo funciona?",
        "Empresa del sector {sector} consulta por servicios de capacitación",
        "Quiero información sobre convenios empresariales y prácticas preprofesionales",
        "Somos una firma de {sector} y buscamos egresados para vacantes",
        "Nuestra empresa necesita cotizar cursos corporativos",
    ],
    "aliado": [
        "Quisiera proponer una alianza estratégica con InkaLab",
        "Hola, represento a una ONG y buscamos proyectos conjuntos",
        "Somos aliados potenciales para experiencias de turismo vivencial",
        "Nos interesa ser aliado institucional para investigaciones",
        "Buscamos alianzas para emprendimiento e innovación educativa",
        "Fundación interesada en colaborar con proyectos sociales",
        "Queremos firmar un convenio de cooperación interinstitucional",
        "Agencia de viajes propone alianza con la unidad de innovación",
    ],
    "egresado": [
        "Hola, soy egresado de la promoción {anio} y quiero actualizar mis datos",
        "Soy exalumno de {carrera}, hay actividades para egresados?",
        "Egresado del instituto consulta por certificados de estudios",
        "Quiero participar en la red de egresados, soy de {carrera}",
        "Soy graduado de la promoción {anio}, necesito constancias",
        "Exalumno consulta si hay descuentos en cursos para egresados",
        "Egresado de {carrera} quiere colaborar con mentorías",
        "Soy egresado y deseo compartir mi experiencia laboral",
    ],
}

APERTURAS = ["", "Buenos días, ", "Buenas tardes, ", "Hola, ", "Estimados, ", "Saludos, "]
CIERRES = ["", " Gracias de antemano.", " Quedo atento.", " Por favor respóndanme.",
           " Agradeceré su apoyo.", " Espero su respuesta."]

# Mensajes ambiguos que en la realidad llegan por cualquier canal y no
# permiten clasificar con certeza: introducen error irreducible realista.
AMBIGUOS = [
    "Hola, tengo una consulta",
    "Buenas tardes, quisiera información",
    "Necesito apoyo por favor",
    "Alguien me puede ayudar?",
    "Buenos días, una pregunta",
    "Quisiera hablar con un asesor",
    "Tengo una duda, quién me atiende",
    "Hola, están atendiendo?",
]

CARRERAS = ["computación e informática", "contabilidad", "administración",
            "turismo", "enfermería técnica", "hotelería"]
COLEGIOS = ["Garcilazo", "Ciencias", "Salesianos", "La Salle", "San Luis Gonzaga", "Túpac Amaru"]
SECTORES = ["minería", "turismo", "banca", "comercio", "construcción", "salud"]
ANIOS = ["2018", "2019", "2020", "2021", "2022"]


def generar_mensajes(por_clase: int = 500):
    textos, etiquetas = [], []
    for tipo, plantillas in PLANTILLAS.items():
        for _ in range(por_clase):
            p = random.choice(plantillas)
            mensaje = p.format(
                carrera=random.choice(CARRERAS),
                colegio=random.choice(COLEGIOS),
                sector=random.choice(SECTORES),
                anio=random.choice(ANIOS),
            )
            mensaje = random.choice(APERTURAS) + mensaje + random.choice(CIERRES)
            textos.append(mensaje)
            etiquetas.append(tipo)

    # ~8% de mensajes ambiguos con etiqueta aleatoria: en la realidad estos
    # mensajes no permiten clasificar con certeza (ruido de etiqueta realista,
    # el bot los resuelve con baja confianza).
    clases = list(PLANTILLAS.keys())
    n_ambiguos = int(len(textos) * 0.08)
    for _ in range(n_ambiguos):
        textos.append(random.choice(AMBIGUOS))
        etiquetas.append(random.choice(clases))

    pares = list(zip(textos, etiquetas))
    random.shuffle(pares)
    textos, etiquetas = (list(x) for x in zip(*pares))
    return textos, etiquetas

def main():
    artifacts = os.path.join("ml", "artifacts")
    os.makedirs(artifacts, exist_ok=True)

    textos, etiquetas = generar_mensajes()
    X_train, X_test, y_train, y_test = train_test_split(
        textos, etiquetas, test_size=0.2, stratify=etiquetas, random_state=SEED
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=1000, C=10.0)),
    ])
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)
    confianza = y_prob.max(axis=1)

    reporte = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    metricas = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "f1_macro": round(float(f1_score(y_test, y_pred, average="macro")), 4),
        "confianza_promedio": round(float(confianza.mean()), 4),
        "por_clase": {
            c: {
                "precision": round(v["precision"], 4),
                "recall": round(v["recall"], 4),
                "f1": round(v["f1-score"], 4),
                "soporte": int(v["support"]),
            }
            for c, v in reporte.items() if c in PLANTILLAS
        },
        "ejemplos_entrenamiento": len(X_train),
        "ejemplos_test": len(X_test),
    }
    print(f"NLP accuracy={metricas['accuracy']} f1_macro={metricas['f1_macro']}")

    joblib.dump(pipeline, os.path.join(artifacts, "nlp_model.joblib"))
    with open(os.path.join(artifacts, "nlp_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metricas, f, ensure_ascii=False, indent=2)
    print(f"Artefactos guardados en {artifacts}/")


if __name__ == "__main__":
    main()
