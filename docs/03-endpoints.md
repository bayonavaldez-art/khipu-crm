# 3. Endpoints de la API REST

Base local: `http://localhost:8000` · Documentación interactiva: `/docs`
(Swagger autogenerado por FastAPI, cumple el entregable "endpoints
documentados").

Todos los endpoints —excepto `/auth/login` y `/health`— requieren el header
`Authorization: Bearer <token JWT>`.

## 3.1 Autenticación

| Método | Ruta | Recibe | Devuelve |
|---|---|---|---|
| POST | `/auth/login` | `{username, password}` | `{access_token, token_type, rol, full_name}` |
| GET | `/auth/me` | — | datos del usuario autenticado |

## 3.2 Contactos (RF01)

| Método | Ruta | Recibe | Devuelve |
|---|---|---|---|
| GET | `/contactos` | query: `q`, `tipo`, `estado`, `limite`, `offset` | lista de contactos |
| POST | `/contactos` | `{nombre, tipo, telefono?, correo?, canal_origen?, procedencia?, notas?}` | contacto creado (201) · *rol admisión+* |
| GET | `/contactos/{id}` | — | contacto |
| PUT | `/contactos/{id}` | campos a actualizar | contacto actualizado · *rol admisión+* |
| DELETE | `/contactos/{id}` | — | 204 · *solo admin* |
| GET | `/contactos/{id}/interacciones` | — | historial de interacciones |
| POST | `/contactos/{id}/interacciones` | `{tipo, comentario?, tiempo_respuesta_horas?}` | interacción creada (201) |

## 3.3 Oportunidades (RF02)

| Método | Ruta | Recibe | Devuelve |
|---|---|---|---|
| GET | `/oportunidades` | query: `etapa`, `contacto_id`, `limite`, `offset` | lista con score persistido |
| POST | `/oportunidades` | `{contacto_id, titulo, etapa?, monto_estimado?}` | oportunidad creada (201) |
| PUT | `/oportunidades/{id}` | `{titulo?, etapa?, monto_estimado?, estado?}` | oportunidad actualizada |
| POST | `/oportunidades/{id}/score` | — | `{probabilidad_conversion, recomendacion, variables_usadas}` — calcula con ML sobre el historial real y persiste el score |

## 3.4 Módulo de IA

| Método | Ruta | Recibe | Devuelve |
|---|---|---|---|
| POST | `/ml/score` | `{tipo_contacto, canal_origen, etapa_embudo, num_interacciones, tiempo_respuesta_promedio, dias_sin_interaccion}` | `{probabilidad_conversion, recomendacion, variables_usadas}` |
| POST | `/ml/classify` | `{mensaje, crear_contacto?, nombre_contacto?}` · *rol admisión+* | `{tipo_contacto, confianza, contacto_id?}` |
| GET | `/ml/model-info` | — | métricas de evaluación de ambos modelos |

## 3.5 Tareas, campañas y alertas (RF03)

| Método | Ruta | Recibe | Devuelve |
|---|---|---|---|
| GET | `/tareas` | query: `estado` | lista de tareas |
| POST | `/tareas` | `{titulo, fecha_limite?, contacto_id?}` | tarea creada (201) |
| PUT | `/tareas/{id}/completar` | — | tarea marcada como hecha |
| GET | `/campanas` · POST `/campanas` | `{nombre, fecha_inicio?, fecha_fin?, objetivo?}` | campañas |
| GET | `/alertas` | — | oportunidades abiertas con más de N días sin interacción (N configurable) |

## 3.6 Dashboard e infraestructura

| Método | Ruta | Devuelve |
|---|---|---|
| GET | `/dashboard` | embudo, contactos por tipo, tasa de conversión, monto ganado, score promedio, tareas pendientes, alertas |
| GET | `/health` | estado del servicio (healthcheck de Render/Docker) |

## 3.7 Códigos de error

| Código | Caso | Ejemplo |
|---|---|---|
| 400/422 | validación de entrada (Pydantic) | tipo de contacto fuera del dominio, correo mal formado |
| 401 | sin token, token expirado o inválido | acceso sin login |
| 403 | rol insuficiente | rol `lector` intentando crear |
| 404 | recurso inexistente | contacto/ oportunidad / tarea con id inválido |

Colección Postman: la UI de Swagger (`/docs`) permite ejecutar todos los
endpoints desde el navegador ("Try it out"), incluido el login para obtener
el token.
