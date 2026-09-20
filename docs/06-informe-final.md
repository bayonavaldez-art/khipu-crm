# 6. Informe final — Khipu CRM Académico-Comercial

**Curso:** Desarrollo de Sistemas Inteligentes II (2025-2)
**Estudiante:** Bayona Valdez, Fany · **Docente:** Poma Enrríquez, Genaro Raúl
**Fecha:** setiembre 2026 · **Instituto Superior Privado Khipu — Cusco**

---

## 1. Resumen ejecutivo

Las áreas de Admisión, Convenios e InkaLab de Khipu pierden oportunidades de
conversión porque la información de contactos e interacciones está dispersa
en hojas de cálculo, WhatsApp, correos y agendas personales, sin mecanismo
que priorice automáticamente a los contactos con mayor probabilidad de
conversión ni que alerte sobre seguimientos atrasados.

Este proyecto entrega una **aplicación web inteligente** que resuelve ese
problema: un CRM institucional con **scoring predictivo de conversión
(machine learning)**, **clasificación automática de mensajes (NLP)** y
**alertas de seguimiento**, desplegado en staging y cubierto por 38 pruebas
automatizadas.

## 2. Arquitectura

Aplicación web de tres capas (detalle y diagramas en `01-arquitectura.md`):

- **Interfaz web** (HTML/JS + Chart.js): login, dashboard con embudo,
  contactos, oportunidades con score, tareas, alertas y KhipuBot.
- **Backend FastAPI** (Python): API REST con autenticación JWT y roles,
  CRUD de contactos/interacciones/oportunidades/tareas/campañas, dashboard y
  endpoints del módulo de IA. Swagger autogenerado en `/docs`.
- **Módulo de IA** (scikit-learn): modelos entrenados fuera de línea,
  artefactos versionados y servidos en línea con carga singleton.
- **Base de datos** relacional: SQLite en desarrollo y PostgreSQL en el
  despliegue (SQLAlchemy como capa de abstracción).

## 3. Modelo de inteligencia artificial

### 3.1 Scoring predictivo de conversión (RF02)

**Problema:** clasificación binaria — dado el comportamiento de una
oportunidad, ¿se convertirá (matrícula / convenio firmado)?

**Datos:** 4 000 registros sintéticos que simulan el histórico centralizado
(44.6 % de conversión), con variables: tipo de contacto, canal de origen,
etapa del embudo, número de interacciones, tiempo promedio de respuesta (h)
y días sin interacción.

**Preparación de datos (documentada en el código `ml/train_scoring.py`):**

1. *Limpieza:* 20 duplicados eliminados; 46 outliers (tiempos de respuesta
   > 720 h) convertidos a nulos; 245 nulos imputados con la mediana.
2. *Codificación y normalización:* one-hot para categóricas; estandarización
   z-score para numéricas (ColumnTransformer).
3. *Selección de variables:* las 6 variables del dominio mostraron poder
   predictivo en el análisis de correlación; se descartaron identificadores
   heredados sin valor predictivo.

**Entrenamiento y comparación** (split estratificado 75/25, seed 42):

| Modelo | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| Regresión Logística ✅ | **0.822** | 0.814 | 0.778 | **0.795** | **0.902** |
| Random Forest (300) | 0.811 | — | — | 0.781 | 0.886 |

Se seleccionó **Regresión Logística** por mayor F1 y ROC-AUC, y por
interpretabilidad: los coeficientes confirman que respuestas rápidas, más
interacciones y etapas avanzadas aumentan la probabilidad — coherente con el
negocio y explicable a Admisión/Convenios. Matriz de confusión (test):
VN 476, FP 79, FN 99, VP 346.

### 3.2 Clasificación NLP — KhipuBot (RF01)

Clasificador de mensajes entrantes en 5 tipos de contacto (TF-IDF n-gramas
1-2 + LogisticRegression), entrenado con 2 700 mensajes simulados que
incluyen ~8 % de mensajes ambiguos con etiqueta aleatoria (ruido realista).

**Resultado:** accuracy **0.944**, F1 macro **0.945** (por clase:
postulante 0.97, colegio 0.93, empresa 0.93, aliado 0.95, egresado 0.95).
La API `/ml/classify` devuelve además la confianza; por debajo de 0.5 la
interfaz marca "revisar manualmente".

### 3.3 Recomendación de próxima acción

Módulo heurístico que traduce el score en acción operativa (agendar cierre,
llamar y enviar información, reactivar o descartar), cruzando la probabilidad
con los días sin interacción (urgencia).

## 4. Pruebas

40 pruebas automatizadas, todas aprobadas (~1.5 s): 11 unitarias del modelo
(umbrales de métricas, coherencia de predicciones, clasificación por clase,
rendimiento: 100 scores < 3 s) y 29 funcionales de la API (login, JWT,
roles, CRUD, interacciones, scoring persistido, KhipuBot, tareas, alertas,
dashboard, códigos de error 401/403/404/422). Plan y evidencia:
`04-plan-de-pruebas.md`.

## 5. Seguridad

Checklist completo en `05-checklist-seguridad.md`: validación estricta de
inputs con Pydantic (regex de dominio, rangos, longitudes), mensajes de error
genéricos (login sin revelar el campo fallido), credenciales fuera del código
fuente (variables de entorno + `.env.example`, `.env` ignorado por Git),
contraseñas con PBKDF2-HMAC-SHA256 (120 000 iteraciones, comparación
constante), JWT con expiración y jerarquía de roles
(lector < admisión < gestor < admin) verificada por pruebas.

## 6. Despliegue

- **Docker:** `Dockerfile` + `docker-compose.yml` (app + PostgreSQL).
- **Staging:** blueprint `render.yaml` para Render (web service Docker +
  PostgreSQL). Guía paso a paso en `07-despliegue.md`.
- Endpoint de healthcheck `/health` para la plataforma.

URL de staging: `https://khipu-crm.onrender.com` *(actualizar al desplegar)*.

## 7. Conclusiones

- Se cumplió el objetivo: un CRM web funcional cuyo diferencial de IA no solo
  almacena datos, sino que **prioriza** contactos y **sugiere** acciones.
- El modelo de scoring alcanza 0.90 ROC-AUC con 6 variables operativas
  sencillas, lo que lo hace explicable y fácil de adoptar por los usuarios.
- El cuello de botella real identificado es la calidad del dato: la
  centralización de interacciones es condición para que el scoring aporte
  valor (como anticipó el análisis de preparación de datos).
- Trabajo futuro: reentrenar periódicamente con datos reales, integrar
  WhatsApp Business API para KhipuBot, y conectar con la cartera DTA
  (Khipu DataBoard, Khipu ID).
