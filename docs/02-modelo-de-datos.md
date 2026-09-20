# 2. Modelo de datos

Implementado con SQLAlchemy en `app/models.py` (ORM). Motor: SQLite en
desarrollo, PostgreSQL en producción.

## 2.1 Diagrama entidad-relación

```mermaid
erDiagram
    CONTACTO ||--o{ INTERACCION : "genera"
    CONTACTO ||--o{ OPORTUNIDAD : "abre"
    CONTACTO ||--o{ TAREA : "involucra"

    CONTACTO {
        int id PK
        string nombre
        string tipo "postulante|colegio|empresa|aliado|egresado"
        string telefono
        string correo
        string canal_origen "whatsapp|web|correo|presencial"
        string procedencia
        string estado "activo|inactivo"
        text notas
        datetime creado
    }
    INTERACCION {
        int id PK
        int contacto_id FK
        string tipo "mensaje|llamada|reunion|correo|envio_informacion"
        datetime fecha
        string responsable
        text comentario
        float tiempo_respuesta_horas "variable del modelo de IA"
    }
    OPORTUNIDAD {
        int id PK
        int contacto_id FK
        string titulo
        string etapa "nuevo|contactado|negociacion|ganado|perdido"
        float monto_estimado
        string estado "abierta|ganada|perdida"
        float score_ia "probabilidad de conversion (ML)"
        datetime score_actualizado
        datetime creada
    }
    CAMPANA {
        int id PK
        string nombre
        datetime fecha_inicio
        datetime fecha_fin
        string objetivo
    }
    TAREA {
        int id PK
        int contacto_id FK
        string titulo
        string responsable
        datetime fecha_limite
        string estado "pendiente|hecha"
    }
    USUARIO {
        int id PK
        string username UK
        string password_hash
        string full_name
        string rol "admin|gestor|admision|lector"
        bool activo
    }
```

## 2.2 Relación con el modelo de IA

Las tablas transaccionales alimentan el modelo de scoring con las variables
definidas en la fase de preparación de datos:

| Variable del modelo | Origen en la base de datos |
|---|---|
| `tipo_contacto` | `contactos.tipo` |
| `canal_origen` | `contactos.canal_origen` |
| `etapa_embudo` | `oportunidades.etapa` |
| `num_interacciones` | `COUNT(interacciones)` del contacto |
| `tiempo_respuesta_promedio` | promedio de `interacciones.tiempo_respuesta_horas` |
| `dias_sin_interaccion` | hoy − fecha de la última interacción |
| `convertido` (target del entrenamiento) | etiqueta del histórico: se matriculó / firmó convenio |

## 2.3 Integridad

- Claves foráneas con borrado en cascada desde contacto (sus interacciones y
  oportunidades se eliminan con él).
- Campos categóricos restringidos por validación Pydantic (ver schemas) —
  la base solo recibe valores del dominio permitido.
