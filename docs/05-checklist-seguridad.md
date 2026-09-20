# 5. Checklist de seguridad básica

Requisito del entregable N.° 3 de las bases del curso. Estado del sistema:

## 5.1 Validación de inputs

| Práctica | Implementación | Verificación |
|---|---|---|
| Esquemas estrictos en todos los endpoints de escritura | Pydantic (`app/schemas.py`) | prueba F14/F15 (422) |
| Campos categóricos restringidos a valores del dominio (regex) | tipo de contacto, canal, etapa, estado | pruebas U/F |
| Longitudes máximas en todos los campos de texto | `Field(max_length=...)` | evita almacenamiento arbitrario |
| Rangos numéricos acotados (monto ≥ 0, horas ≤ 1 año) | `Field(ge=..., le=...)` | prueba F14 |
| Correo validado como email real | `EmailStr` + email-validator | prueba F15 |
| Parámetros de paginación acotados (limite ≤ 200) | `Query(..., le=200)` | evita consultas masivas |

## 5.2 Manejo de errores

| Práctica | Implementación |
|---|---|
| Sin stack traces al cliente | FastAPI devuelve JSON `{detail}` controlado |
| Login con mensaje genérico | "Credenciales incorrectas" — no revela si falló usuario o clave |
| 404 para recursos inexistentes (sin datos internos) | todos los routers |
| Errores de JWT diferenciados en el servidor, genéricos para el cliente | `app/auth.py` |
| La interfaz muestra los errores de la API sin romperse | `static/js/api.js` (try/catch + toast) |

## 5.3 Credenciales y secretos

| Práctica | Implementación |
|---|---|
| Ninguna credencial en el código fuente | `SECRET_KEY`, `DATABASE_URL` etc. vía variables de entorno (`app/config.py`) |
| Plantilla de configuración sin secretos reales | `.env.example` |
| `.env` excluido del repositorio | `.gitignore` |
| Contraseñas almacenadas con hash + salt | PBKDF2-HMAC-SHA256, 120 000 iteraciones (`app/auth.py`) |
| Comparación resistente a timing attacks | `hmac.compare_digest` |
| Tokens JWT con expiración (8 h configurable) | `ACCESS_TOKEN_EXPIRE_MINUTES` |

## 5.4 Control de acceso (RNF01)

| Práctica | Implementación | Verificación |
|---|---|---|
| Autenticación obligatoria en toda la API (excepto login/health) | dependencia `get_current_user` | prueba F05 |
| Roles con jerarquía: lector < admisión < gestor < admin | `require_rol()` | pruebas F07/F08/F16 |
| Escrituras requieren rol admisión o superior | routers | F07 |
| Eliminación solo admin | router contactos | F16 |
| Tokens inválidos/expirados rechazados | decodificación + verificación de usuario activo | F06 |

## 5.5 Frontend

| Práctica | Implementación |
|---|---|
| Token en localStorage y logout que lo elimina | `static/js/api.js` |
| Token inválido redirige al login automáticamente | interceptor 401 |
| Todo contenido dinámico se escapa contra XSS | función `esc()` en `views.js` |

## 5.6 Pendientes para producción real (fuera del alcance académico)

- HTTPS: lo provee la plataforma (Render termina TLS).
- Rate limiting en `/auth/login` (p. ej. `slowapi`) — recomendado si el
  sistema se expone públicamente de forma permanente.
- Rotación programada de `SECRET_KEY`.
- Cifrado en reposo de campos sensibles — lo provee el disco gestionado de la
  base de datos en la nube.
