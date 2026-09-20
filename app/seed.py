"""Carga datos de demostración (usuarios, contactos, oportunidades...).

Se ejecuta solo si la base está vacía. Las contraseñas demo están hasheadas
con PBKDF2 igual que en producción; se documentan en el README solo para la
demo académica.
"""
import datetime as dt
import random

from sqlalchemy.orm import Session

from app.auth import hash_password
from app.models import Campana, Contacto, Interaccion, Oportunidad, Tarea, Usuario

USUARIOS_DEMO = [
    ("admin", "Admin@123", "Administrador del Sistema", "admin"),
    ("gestor", "Gestor@123", "Gestor Comercial", "gestor"),
    ("admision", "Admision@123", "Equipo de Admisión", "admision"),
    ("lector", "Lector@123", "Dirección General (solo lectura)", "lector"),
]

CONTACTOS_DEMO = [
    ("María Quispe Huamán", "postulante", "987654321", "maria.quispe@gmail.com", "whatsapp", "Colegio Ciencias"),
    ("Jorge Luis Mamani", "postulante", "987112233", "jorge.mamani@gmail.com", "web", "Colegio Salesianos"),
    ("Lucía Farfán Baca", "postulante", "976554433", "lucia.farfan@gmail.com", "correo", "Feria Khipu 2026"),
    ("I.E. Garcilazo de la Vega", "colegio", "084234567", "direccion@garcilazo.edu.pe", "correo", "Cusco centro"),
    ("I.E.P. La Salle", "colegio", "084238899", "academic@lasalle.edu.pe", "presencial", "Visita institucional"),
    ("Turismo Andino SAC", "empresa", "984123456", "contacto@turismoandino.com", "web", "Convenio prácticas"),
    ("Minera Qori Koyllor", "empresa", "984777888", "rrhh@qorikoyllor.com", "correo", "Bolsa de trabajo"),
    ("ONG Sumak Kawsay", "aliado", "973222111", "proyectos@sumak.org.pe", "whatsapp", "Proyectos sociales"),
    ("Agencia Viajes Inkari", "aliado", "973999888", "alianzas@inkari.com", "whatsapp", "InkaLab experiencias"),
    ("Pedro Condori Rojas", "egresado", "966888777", "pedro.condori@gmail.com", "correo", "Promoción 2019"),
    ("Rosa Huillca Mamani", "egresado", "966777666", "rosa.huillca@gmail.com", "web", "Promoción 2021"),
    ("Kevin Sullca Puma", "postulante", "912345678", "kevin.sullca@gmail.com", "whatsapp", "Campaña Julio 2026"),
    ("I.E. Túpac Amaru", "colegio", "084255566", "secretaria@tupacamaru.edu.pe", "presencial", "San Sebastián"),
    ("Constructora Wiracocha", "empresa", "984555444", "gerencia@wiracocha.pe", "correo", "Capacitación corporativa"),
    ("Ana Paucar Sisa", "postulante", "943211234", "ana.paucar@gmail.com", "web", "Anuncio Instagram"),
    ("Universidad Altiplano", "aliado", "951444333", "convenios@altiplano.edu.pe", "correo", "Investigación conjunta"),
]

# (índice de contacto, tipo, hace cuántos días, comentario, horas de respuesta)
INTERACCIONES_DEMO = [
    (0, "mensaje", 20, "Consulta por carrera de Computación e Informática", 2.5),
    (0, "llamada", 15, "Se explicó requisitos y costos; muy interesada", 24.0),
    (0, "reunion", 6, "Visita al campus con sus padres", 48.0),
    (1, "mensaje", 18, "Consulta por modalidad de estudios", 30.0),
    (1, "envio_informacion", 10, "Se envió brochure de carreras técnicas", 72.0),
    (2, "correo", 25, "Solicita información de admisión", 96.0),
    (3, "reunion", 40, "Reunión con dirección para coordinar charla", 24.0),
    (3, "llamada", 12, "Confirmación de fecha de visita de alumnos", 4.0),
    (4, "reunion", 8, "Agenda de visita guiada para 45 estudiantes", 6.0),
    (5, "correo", 30, "Propuesta de convenio para prácticas", 120.0),
    (5, "reunion", 9, "Presentación del modelo de convenios", 24.0),
    (6, "mensaje", 22, "Búsqueda de técnicos en contabilidad", 8.0),
    (7, "reunion", 45, "Exploración de proyectos sociales conjuntos", 24.0),
    (8, "mensaje", 14, "Interés en experiencias InkaLab para turistas", 3.0),
    (8, "llamada", 5, "Cotización de experiencia vivencial", 5.0),
    (9, "correo", 60, "Solicitud de certificados", 240.0),
    (10, "mensaje", 35, "Quiere unirse a la red de egresados", 12.0),
    (11, "mensaje", 2, "Consulta por becas", 1.5),
    (12, "llamada", 16, "Coordinación de feria vocacional", 20.0),
    (13, "correo", 50, "Solicitud de capacitación en seguridad", 168.0),
    (14, "mensaje", 1, "Consulta requisitos de inscripción", 2.0),
    (15, "reunion", 28, "Propuesta de investigación aplicada", 48.0),
]

# (índice de contacto, título, etapa, monto)
OPORTUNIDADES_DEMO = [
    (0, "Matrícula Computación e Informática 2026-2", "negociacion", 3800.0),
    (1, "Matrícula Contabilidad 2026-2", "contactado", 3200.0),
    (2, "Matrícula Administración 2026-2", "nuevo", 3200.0),
    (3, "Charla vocacional + visita I.E. Garcilazo", "negociacion", 0.0),
    (4, "Visita guiada I.E.P. La Salle", "contactado", 0.0),
    (5, "Convenio de prácticas Turismo Andino", "negociacion", 5000.0),
    (6, "Convenio bolsa de trabajo Minera Qori", "contactado", 0.0),
    (7, "Proyecto social conjunto ONG Sumak", "nuevo", 0.0),
    (8, "Experiencia vivencial InkaLab - Inkari", "negociacion", 7500.0),
    (9, "Membresía red de egresados", "ganado", 150.0),
    (11, "Matrícula Enfermería Técnica 2026-2", "nuevo", 3600.0),
    (12, "Feria vocacional I.E. Túpac Amaru", "ganado", 800.0),
    (13, "Capacitación corporativa Wiracocha", "perdido", 4000.0),
    (14, "Matrícula Turismo 2026-2", "contactado", 3400.0),
]

CAMPANAS_DEMO = [
    ("Campaña de Admisión 2026-2", "2026-08-01", "2026-10-15",
     "Captación de postulantes para el semestre 2026-2"),
    ("Feria Vocacional Colegios Cusco", "2026-07-15", "2026-09-15",
     "Visitas y charlas en colegios de la región"),
    ("Convenios Empresariales InkaLab", "2026-06-01", "2026-12-31",
     "Firma de convenios con empresas aliadas"),
]

TAREAS_DEMO = [
    (0, "Llamar a María para confirmar matrícula", 1),
    (1, "Enviar requisitos de inscripción a Jorge", 2),
    (8, "Preparar cotización Inkari", 0),
    (3, "Confirmar fecha de visita Garcilazo", -1),
    (11, "Seguimiento becas Kevin", 3),
    (None, "Revisar reportes de campaña semanal", 5),
]


def seed_demo(db: Session) -> None:
    if db.query(Usuario).count() > 0:
        return  # ya inicializada

    random.seed(42)
    ahora = dt.datetime.now()

    # Usuarios
    for username, password, nombre, rol in USUARIOS_DEMO:
        db.add(Usuario(
            username=username,
            password_hash=hash_password(password),
            full_name=nombre,
            rol=rol,
        ))

    # Contactos
    contactos = []
    for nombre, tipo, tel, correo, canal, proc in CONTACTOS_DEMO:
        c = Contacto(nombre=nombre, tipo=tipo, telefono=tel, correo=correo,
                     canal_origen=canal, procedencia=proc)
        db.add(c)
        contactos.append(c)
    db.flush()  # asigna los IDs antes de usarlos en las relaciones

    # Interacciones (fechas relativas a hoy)
    for idx, tipo, hace_dias, comentario, horas in INTERACCIONES_DEMO:
        db.add(Interaccion(
            contacto_id=contactos[idx].id,
            tipo=tipo,
            fecha=ahora - dt.timedelta(days=hace_dias),
            responsable="Equipo de Admisión",
            comentario=comentario,
            tiempo_respuesta_horas=horas,
        ))

    # Oportunidades
    for idx, titulo, etapa, monto in OPORTUNIDADES_DEMO:
        estado = {"ganado": "ganada", "perdido": "perdida"}.get(etapa, "abierta")
        db.add(Oportunidad(
            contacto_id=contactos[idx].id,
            titulo=titulo,
            etapa=etapa,
            monto_estimado=monto,
            estado=estado,
        ))

    # Campañas
    for nombre, ini, fin, objetivo in CAMPANAS_DEMO:
        db.add(Campana(
            nombre=nombre,
            fecha_inicio=dt.datetime.fromisoformat(ini),
            fecha_fin=dt.datetime.fromisoformat(fin),
            objetivo=objetivo,
        ))

    # Tareas
    for contacto_idx, titulo, en_dias in TAREAS_DEMO:
        db.add(Tarea(
            contacto_id=contactos[contacto_idx].id if contacto_idx is not None else None,
            titulo=titulo,
            responsable="Equipo de Admisión",
            fecha_limite=ahora + dt.timedelta(days=en_dias),
            estado="pendiente" if en_dias >= 0 else "hecha",
        ))

    db.commit()
