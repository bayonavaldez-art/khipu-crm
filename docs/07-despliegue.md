# 7. Guía de despliegue

## 7.1 Opción A — Render (recomendada para la entrega)

Requisito de las bases: sistema accesible fuera del entorno local. Render
ofrece plan gratuito y el repo ya incluye el blueprint `render.yaml`.

1. Subir el repositorio a GitHub (público o compartido con el docente).
2. Entrar a [render.com](https://render.com) → **New → Blueprint** →
   seleccionar el repositorio.
3. Render detecta `render.yaml` y crea:
   - **Web service** (Docker): `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **PostgreSQL** (free): queda enlazado como `DATABASE_URL`.
4. En el entorno del servicio, definir `SECRET_KEY` (uno nuevo, generado con
   `openssl rand -hex 32`).
5. Esperar el build (~3-5 min) y verificar `https://<nombre>.onrender.com/health`.
6. Actualizar la URL en el README y en este documento.

> Nota: en el plan gratuito el servicio "duerme" tras inactividad; la primera
> carga puede tardar ~30 s. Suficiente para la demo.

## 7.2 Opción B — Docker local (staging propio)

```bash
docker compose up --build
# app:      http://localhost:8000
# postgres: puerto 5432 (interno de la red de compose)
```

`docker-compose.yml` levanta dos contenedores: la aplicación y PostgreSQL 16,
con variables de entorno separadas del código.

## 7.3 Variables de entorno requeridas

| Variable | Uso | Ejemplo |
|---|---|---|
| `SECRET_KEY` | firma de los JWT | salida de `openssl rand -hex 32` |
| `DATABASE_URL` | conexión de la base | `postgresql://usuario:clave@host:5432/khipu` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | validez del token | `480` |
| `ALERTA_DIAS_SIN_INTERACCION` | umbral de alertas RF03 | `7` |

## 7.4 Verificación post-despliegue

1. `GET /health` → `{"status":"ok"}`.
2. Login con `admin / Admin@123` desde la interfaz.
3. Dashboard carga embudo y gráficos.
4. "Calcular score" en una oportunidad devuelve probabilidad y recomendación.
5. KhipuBot clasifica un mensaje de prueba.
6. `python -m pytest tests/ -v` en local sigue en verde.
