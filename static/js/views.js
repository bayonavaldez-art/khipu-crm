// Vistas del CRM: dashboard, contactos, oportunidades, tareas y KhipuBot.
// Interfaz funcional sin frameworks (cumple el alcance del curso).

const Views = (() => {
  let graficos = {}; // instancias Chart.js activas

  const esc = (s) =>
    String(s ?? "").replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const fmtFecha = (iso) =>
    iso ? new Date(iso).toLocaleDateString("es-PE", { day: "2-digit", month: "short", year: "numeric" }) : "—";

  const fmtMonto = (n) => "S/ " + Number(n || 0).toLocaleString("es-PE");

  let toastTimer = null;
  function toast(mensaje) {
    const t = document.getElementById("toast");
    t.textContent = mensaje;
    t.hidden = false;
    // Duración proporcional al texto: 6 s de base y +60 ms por cada carácter
    // sobre 60, tope 14 s — así las recomendaciones largas del score se leen
    // completas. Un clic sobre la notificación la cierra antes.
    clearTimeout(toastTimer);
    const duracion = Math.min(14000, 6000 + Math.max(0, mensaje.length - 60) * 60);
    toastTimer = setTimeout(() => (t.hidden = true), duracion);
  }
  document.addEventListener("click", (e) => {
    const t = document.getElementById("toast");
    if (e.target === t && !t.hidden) {
      clearTimeout(toastTimer);
      t.hidden = true;
    }
  });

  function modal(html) {
    const capa = document.createElement("div");
    capa.className = "form-modal";
    capa.innerHTML = `<div class="modal-caja">${html}</div>`;
    capa.addEventListener("click", (e) => { if (e.target === capa) capa.remove(); });
    document.body.appendChild(capa);
    return capa;
  }

  const claseScore = (p) => (p >= 0.7 ? "score-alto" : p >= 0.4 ? "score-medio" : "score-bajo");

  // ================= DASHBOARD =================
  async function dashboard(el) {
    const d = await API.get("/dashboard");
    el.innerHTML = `
      <h2>Dashboard</h2>
      <p class="desc">Indicadores de contactos, embudo de oportunidades y seguimiento.</p>
      <div class="grid-cards">
        <div class="card"><div class="label">Contactos</div>
          <div class="valor">${d.total_contactos}</div>
          <div class="extra">${Object.entries(d.contactos_por_tipo).map(([k, v]) => `${k}: ${v}`).join(" · ")}</div></div>
        <div class="card"><div class="label">Tasa de conversión</div>
          <div class="valor">${d.tasa_conversion_pct}%</div>
          <div class="extra">ganadas / cerradas</div></div>
        <div class="card"><div class="label">Monto ganado (est.)</div>
          <div class="valor">${fmtMonto(d.monto_ganado_estimado)}</div>
          <div class="extra">oportunidades en etapa ganado</div></div>
        <div class="card"><div class="label">Score IA promedio</div>
          <div class="valor">${d.score_promedio != null ? (d.score_promedio * 100).toFixed(0) + "%" : "—"}</div>
          <div class="extra">${d.oportunidades_con_score} oportunidades con score</div></div>
        <div class="card"><div class="label">Tareas pendientes</div>
          <div class="valor">${d.tareas_pendientes}</div>
          <div class="extra">${d.alertas_seguimiento} alertas de seguimiento</div></div>
      </div>
      <div class="charts">
        <div class="chart-box"><h3>Embudo de oportunidades</h3>
          <canvas id="chart-embudo" height="220"></canvas></div>
        <div class="chart-box"><h3>Contactos por tipo</h3>
          <canvas id="chart-tipos" height="220"></canvas></div>
      </div>`;

    Object.values(graficos).forEach((g) => g.destroy());
    graficos.embudo = new Chart(document.getElementById("chart-embudo"), {
      type: "bar",
      data: {
        labels: ["Nuevo", "Contactado", "Negociación", "Ganado", "Perdido"],
        datasets: [{
          data: ["nuevo", "contactado", "negociacion", "ganado", "perdido"].map((k) => d.embudo[k] || 0),
          backgroundColor: ["#a8b0c0", "#5163a6", "#c2701d", "#1d7d4f", "#b4493c"],
          borderRadius: 4,
        }],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "#eef0f4" } },
                  x: { grid: { display: false } } },
      },
    });
    graficos.tipos = new Chart(document.getElementById("chart-tipos"), {
      type: "doughnut",
      data: {
        labels: Object.keys(d.contactos_por_tipo),
        datasets: [{
          data: Object.values(d.contactos_por_tipo),
          backgroundColor: ["#5163a6", "#c2701d", "#7c8ab0", "#1d7d4f", "#a8628f"],
          borderColor: "#ffffff",
          borderWidth: 2,
        }],
      },
      options: { plugins: { legend: { position: "right" } }, cutout: "62%" },
    });
  }

  // ================= CONTACTOS =================
  async function contactos(el) {
    el.innerHTML = `
      <h2>Contactos</h2>
      <p class="desc">Postulantes, colegios, empresas, aliados y egresados (RF01).</p>
      <div class="toolbar">
        <input id="c-buscar" placeholder="Buscar por nombre o correo…" style="flex:1">
        <select id="c-tipo">
          <option value="">Todos los tipos</option>
          <option>postulante</option><option>colegio</option>
          <option>empresa</option><option>aliado</option><option>egresado</option>
        </select>
        <button class="btn btn-primary" id="c-nuevo">+ Nuevo contacto</button>
      </div>
      <div id="c-tabla"></div>`;

    const cargarTabla = async () => {
      const q = document.getElementById("c-buscar").value.trim();
      const tipo = document.getElementById("c-tipo").value;
      const datos = await API.get(`/contactos?limite=100${q ? `&q=${encodeURIComponent(q)}` : ""}${tipo ? `&tipo=${tipo}` : ""}`);
      document.getElementById("c-tabla").innerHTML = datos.length ? `
        <table><thead><tr>
          <th>Nombre</th><th>Tipo</th><th>Teléfono</th><th>Correo</th>
          <th>Canal</th><th>Estado</th><th></th>
        </tr></thead><tbody>
          ${datos.map((c) => `
            <tr>
              <td><strong>${esc(c.nombre)}</strong><br>
                  <small style="color:var(--texto-suave)">${esc(c.procedencia || "")}</small></td>
              <td><span class="badge badge-${esc(c.tipo)}">${esc(c.tipo)}</span></td>
              <td>${esc(c.telefono || "—")}</td>
              <td>${esc(c.correo || "—")}</td>
              <td>${esc(c.canal_origen || "—")}</td>
              <td>${esc(c.estado)}</td>
              <td>
                <button class="btn btn-sm btn-primary" data-ver="${c.id}">Interacciones</button>
              </td>
            </tr>`).join("")}
        </tbody></table>` : "<p>No hay contactos con esos filtros.</p>";

      el.querySelectorAll("[data-ver]").forEach((b) =>
        b.addEventListener("click", () => verInteracciones(parseInt(b.dataset.ver), datos.find((x) => x.id == b.dataset.ver))));
    };

    document.getElementById("c-buscar").addEventListener("input", cargarTabla);
    document.getElementById("c-tipo").addEventListener("change", cargarTabla);
    document.getElementById("c-nuevo").addEventListener("click", () => formContacto(cargarTabla));
    await cargarTabla();
  }

  function formContacto(recargar) {
    const capa = modal(`
      <h3>Nuevo contacto</h3>
      <form id="f-contacto">
        <label>Nombre *</label><input name="nombre" required minlength="2">
        <label>Tipo *</label>
        <select name="tipo"><option>postulante</option><option>colegio</option>
          <option>empresa</option><option>aliado</option><option>egresado</option></select>
        <label>Teléfono</label><input name="telefono">
        <label>Correo</label><input name="correo" type="email">
        <label>Canal de origen</label>
        <select name="canal_origen"><option value="whatsapp">whatsapp</option>
          <option value="web">web</option><option value="correo">correo</option>
          <option value="presencial">presencial</option></select>
        <label>Procedencia</label><input name="procedencia" placeholder="Colegio, campaña, ciudad…">
        <label>Notas</label><textarea name="notas" rows="2"></textarea>
        <div class="acciones">
          <button type="button" class="btn btn-linea" data-cerrar>Cancelar</button>
          <button type="submit" class="btn btn-primary">Guardar</button>
        </div>
      </form>`);
    capa.querySelector("[data-cerrar]").addEventListener("click", () => capa.remove());
    capa.querySelector("#f-contacto").addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const cuerpo = Object.fromEntries(fd.entries());
      try {
        await API.post("/contactos", cuerpo);
        capa.remove();
        toast("Contacto creado");
        recargar();
      } catch (err) { toast(err.message); }
    });
  }

  async function verInteracciones(id, contacto) {
    const lista = await API.get(`/contactos/${id}/interacciones`);
    const capa = modal(`
      <h3>Interacciones · ${esc(contacto?.nombre || "")}</h3>
      <p style="color:var(--texto-suave);font-size:.85rem;margin-top:4px">
        Historial de llamadas, mensajes, correos y reuniones.</p>
      <form id="f-inter">
        <label>Tipo</label>
        <select name="tipo"><option>mensaje</option><option>llamada</option>
          <option>reunion</option><option>correo</option><option>envio_informacion</option></select>
        <label>Comentario</label><textarea name="comentario" rows="2" required></textarea>
        <label>Tiempo de respuesta (horas)</label><input name="tiempo" type="number" min="0" step="0.5" value="24">
        <div class="acciones">
          <button type="button" class="btn" style="background:#e2e8f0" data-cerrar>Cerrar</button>
          <button type="submit" class="btn btn-primary">Registrar</button>
        </div>
      </form>
      <div style="margin-top:18px">
        ${lista.length ? lista.map((i) => `
          <div class="card" style="margin-bottom:8px;padding:12px">
            <strong>${esc(i.tipo)}</strong>
            <span style="color:var(--texto-suave);font-size:.8rem"> · ${fmtFecha(i.fecha)} · ${esc(i.responsable || "")}</span>
            ${i.tiempo_respuesta_horas != null ? `<span class="badge badge-nuevo" style="float:right">resp: ${i.tiempo_respuesta_horas} h</span>` : ""}
            <div style="font-size:.85rem;margin-top:6px">${esc(i.comentario || "")}</div>
          </div>`).join("") : "<p>Sin interacciones registradas.</p>"}
      </div>`);
    capa.querySelector("[data-cerrar]").addEventListener("click", () => capa.remove());
    capa.querySelector("#f-inter").addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      try {
        await API.post(`/contactos/${id}/interacciones`, {
          tipo: fd.get("tipo"),
          comentario: fd.get("comentario"),
          tiempo_respuesta_horas: parseFloat(fd.get("tiempo")) || null,
        });
        capa.remove();
        toast("Interacción registrada");
      } catch (err) { toast(err.message); }
    });
  }

  // ================= OPORTUNIDADES =================
  async function oportunidades(el) {
    el.innerHTML = `
      <h2>Oportunidades</h2>
      <p class="desc">Embudo de seguimiento con score predictivo de IA (RF02).</p>
      <div class="toolbar">
        <select id="o-etapa">
          <option value="">Todas las etapas</option>
          <option value="nuevo">nuevo</option><option value="contactado">contactado</option>
          <option value="negociacion">negociación</option><option value="ganado">ganado</option>
          <option value="perdido">perdido</option>
        </select>
        <button class="btn btn-primary" id="o-nueva">+ Nueva oportunidad</button>
      </div>
      <div id="o-tabla"></div>`;

    const cargarTabla = async () => {
      const etapa = document.getElementById("o-etapa").value;
      const datos = await API.get(`/oportunidades?limite=100${etapa ? `&etapa=${etapa}` : ""}`);
      document.getElementById("o-tabla").innerHTML = datos.length ? `
        <table><thead><tr>
          <th>Oportunidad</th><th>Contacto</th><th>Etapa</th><th>Monto est.</th>
          <th>Score IA</th><th></th>
        </tr></thead><tbody>
          ${datos.map((o) => `
            <tr>
              <td><strong>${esc(o.titulo)}</strong></td>
              <td>${esc(o.contacto_nombre || o.contacto_id)}</td>
              <td><span class="badge badge-${esc(o.etapa)}">${esc(o.etapa)}</span></td>
              <td>${fmtMonto(o.monto_estimado)}</td>
              <td>${o.score_ia != null
                    ? `<span class="score-pill ${claseScore(o.score_ia)}">${(o.score_ia * 100).toFixed(0)}%</span>`
                    : "—"}</td>
              <td>
                <button class="btn btn-sm btn-verde" data-score="${o.id}">Calcular score</button>
                <select data-etapa="${o.id}" style="width:auto;padding:4px 8px;font-size:.78rem">
                  ${["nuevo", "contactado", "negociacion", "ganado", "perdido"]
                    .map((e2) => `<option ${e2 === o.etapa ? "selected" : ""}>${e2}</option>`).join("")}
                </select>
              </td>
            </tr>`).join("")}
        </tbody></table>` : "<p>No hay oportunidades con ese filtro.</p>";

      el.querySelectorAll("[data-score]").forEach((b) =>
        b.addEventListener("click", async () => {
          b.disabled = true;
          b.textContent = "Calculando…";
          try {
            const r = await API.post(`/oportunidades/${b.dataset.score}/score`);
            toast(`${(r.probabilidad_conversion * 100).toFixed(0)}% · ${r.recomendacion}`);
            await cargarTabla();
          } catch (err) { toast(err.message); b.disabled = false; b.textContent = "Calcular score"; }
        }));

      el.querySelectorAll("[data-etapa]").forEach((s) =>
        s.addEventListener("change", async () => {
          try {
            await API.put(`/oportunidades/${s.dataset.etapa}`, { etapa: s.value });
            toast("Etapa actualizada");
            await cargarTabla();
          } catch (err) { toast(err.message); }
        }));
    };

    document.getElementById("o-etapa").addEventListener("change", cargarTabla);
    document.getElementById("o-nueva").addEventListener("click", () => formOportunidad(cargarTabla));
    await cargarTabla();
  }

  async function formOportunidad(recargar) {
    const contactos = await API.get("/contactos?limite=200");
    const capa = modal(`
      <h3>Nueva oportunidad</h3>
      <form id="f-op">
        <label>Contacto *</label>
        <select name="contacto_id" required>
          ${contactos.map((c) => `<option value="${c.id}">${esc(c.nombre)} (${esc(c.tipo)})</option>`).join("")}
        </select>
        <label>Título *</label><input name="titulo" required minlength="3"
          placeholder="Ej.: Matrícula Computación 2026-2">
        <label>Etapa</label>
        <select name="etapa"><option>nuevo</option><option>contactado</option>
          <option>negociacion</option><option>ganado</option><option>perdido</option></select>
        <label>Monto estimado (S/)</label><input name="monto_estimado" type="number" min="0" step="0.01" value="0">
        <div class="acciones">
          <button type="button" class="btn btn-linea" data-cerrar>Cancelar</button>
          <button type="submit" class="btn btn-primary">Guardar</button>
        </div>
      </form>`);
    capa.querySelector("[data-cerrar]").addEventListener("click", () => capa.remove());
    capa.querySelector("#f-op").addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      try {
        await API.post("/oportunidades", {
          contacto_id: parseInt(fd.get("contacto_id")),
          titulo: fd.get("titulo"),
          etapa: fd.get("etapa"),
          monto_estimado: parseFloat(fd.get("monto_estimado")) || 0,
        });
        capa.remove();
        toast("Oportunidad creada");
        recargar();
      } catch (err) { toast(err.message); }
    });
  }

  // ================= TAREAS Y ALERTAS =================
  async function tareas(el) {
    // OJO: no llamar "tareas" a la lista local — taparía el nombre de esta
    // función dentro de su propio ámbito (bug "tareas is not a function").
    const [listaTareas, alertas] = await Promise.all([
      API.get("/tareas"),
      API.get("/alertas"),
    ]);
    el.innerHTML = `
      <h2>Tareas y alertas</h2>
      <p class="desc">Seguimientos programados y alertas automáticas de oportunidades sin interacción (RF03).</p>
      <div class="toolbar">
        <button class="btn btn-primary" id="t-nueva">+ Nueva tarea</button>
      </div>
      ${alertas.total ? `
        <h3 style="margin:8px 0">Alertas de seguimiento (${alertas.total}) · más de ${alertas.dias_limite} días sin interacción</h3>
        ${alertas.alertas.map((a) => `
          <div class="alerta-item">
            <strong>${esc(a.titulo)}</strong> · ${esc(a.contacto)} — ${esc(a.mensaje)}
          </div>`).join("")}` : "<p>Sin alertas de seguimiento activas.</p>"}
      <h3 style="margin:20px 0 10px">Tareas</h3>
      ${listaTareas.length ? `
        <table><thead><tr>
          <th>Tarea</th><th>Responsable</th><th>Fecha límite</th><th>Estado</th><th></th>
        </tr></thead><tbody>
          ${listaTareas.map((t) => `
            <tr>
              <td>${esc(t.titulo)}</td>
              <td>${esc(t.responsable || "—")}</td>
              <td>${fmtFecha(t.fecha_limite)}</td>
              <td><span class="badge badge-${esc(t.estado)}">${esc(t.estado)}</span></td>
              <td>${t.estado === "pendiente"
                    ? `<button class="btn btn-sm btn-verde" data-done="${t.id}">Marcar hecha</button>` : ""}</td>
            </tr>`).join("")}
        </tbody></table>` : "<p>Sin tareas registradas.</p>"}`;

    el.querySelectorAll("[data-done]").forEach((b) =>
      b.addEventListener("click", async () => {
        try {
          await API.put(`/tareas/${b.dataset.done}/completar`, {});
          toast("Tarea completada");
          await tareas(el);
        } catch (err) { toast(err.message); }
      }));
    document.getElementById("t-nueva").addEventListener("click", () => formTarea(el));
  }

  async function formTarea(vista) {
    const capa = modal(`
      <h3>Nueva tarea</h3>
      <form id="f-tarea">
        <label>Título *</label><input name="titulo" required minlength="3">
        <label>Fecha límite</label><input name="fecha_limite" type="date">
        <div class="acciones">
          <button type="button" class="btn btn-linea" data-cerrar>Cancelar</button>
          <button type="submit" class="btn btn-primary">Guardar</button>
        </div>
      </form>`);
    capa.querySelector("[data-cerrar]").addEventListener("click", () => capa.remove());
    capa.querySelector("#f-tarea").addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      try {
        await API.post("/tareas", {
          titulo: fd.get("titulo"),
          fecha_limite: fd.get("fecha_limite") ? new Date(fd.get("fecha_limite") + "T12:00:00").toISOString() : null,
        });
        capa.remove();
        toast("Tarea creada");
        await tareas(vista);
      } catch (err) { toast(err.message); }
    });
  }

  // ================= KHIPUBOT (IA) =================
  async function bot(el) {
    el.innerHTML = `
      <h2>KhipuBot · Clasificación inteligente</h2>
      <p class="desc">Simula un mensaje entrante (WhatsApp/web/correo): el modelo NLP
        clasifica el tipo de contacto y puede registrarlo automáticamente (RF01).</p>
      <div class="bot-caja">
        <textarea id="b-mensaje" rows="3"
          placeholder="Ej.: Hola, soy del colegio La Salle y queremos coordinar una visita…"></textarea>
        <div class="toolbar" style="margin-top:10px">
          <input id="b-nombre" placeholder="Nombre del contacto (opcional)" style="flex:1">
          <label style="display:flex;align-items:center;gap:6px;font-size:.85rem">
            <input type="checkbox" id="b-crear" style="width:auto"> Crear contacto
          </label>
          <button class="btn btn-primary" id="b-clasificar">Clasificar mensaje</button>
        </div>
        <div id="b-resultado"></div>
        <div class="card" style="margin-top:24px">
          <h3 style="font-size:.9rem;margin-bottom:8px">Métricas del modelo</h3>
          <div id="b-metricas" style="font-size:.82rem;color:var(--texto-suave)">Cargando…</div>
        </div>
      </div>`;

    document.getElementById("b-clasificar").addEventListener("click", async () => {
      const mensaje = document.getElementById("b-mensaje").value.trim();
      if (mensaje.length < 5) { toast("Escribe un mensaje de al menos 5 caracteres"); return; }
      try {
        const r = await API.post("/ml/classify", {
          mensaje,
          crear_contacto: document.getElementById("b-crear").checked,
          nombre_contacto: document.getElementById("b-nombre").value.trim() || null,
        });
        document.getElementById("b-resultado").innerHTML = `
          <div class="bot-resultado">
            <div>Tipo detectado:
              <span class="badge badge-${esc(r.tipo_contacto)}" style="font-size:.95rem">${esc(r.tipo_contacto)}</span>
            </div>
            <div style="margin-top:8px;font-size:.9rem">
              Confianza: <strong>${(r.confianza * 100).toFixed(1)}%</strong>
              ${r.confianza < 0.5 ? '<span style="color:var(--ambar)"> · baja: revisar manualmente</span>' : ""}
            </div>
            <div class="confianza-barra"><div style="width:${(r.confianza * 100).toFixed(1)}%"></div></div>
            ${r.contacto_id ? `<div style="margin-top:10px;font-size:.85rem">Contacto creado con ID ${r.contacto_id}</div>` : ""}
          </div>`;
        if (r.contacto_id) toast("Contacto creado desde KhipuBot");
      } catch (err) { toast(err.message); }
    });

    // Métricas del modelo (evidencia de evaluación en la propia interfaz)
    try {
      const info = await API.get("/ml/model-info");
      const nlp = info.nlp, sc = info.scoring?.resultados?.[info.scoring.modelo_seleccionado] || {};
      document.getElementById("b-metricas").innerHTML = `
        <strong>NLP:</strong> accuracy ${(nlp.accuracy * 100).toFixed(1)}% ·
        F1 macro ${(nlp.f1_macro * 100).toFixed(1)}% ·
        entrenado con ${nlp.ejemplos_entrenamiento} mensajes<br>
        <strong>Scoring (${esc(info.scoring.modelo_seleccionado)}):</strong>
        accuracy ${(sc.accuracy * 100 ?? 0).toFixed?.(0) ?? sc.accuracy} ·
        F1 ${sc.f1} · ROC-AUC ${sc.roc_auc}`;
    } catch (_) {
      document.getElementById("b-metricas").textContent = "Métricas no disponibles.";
    }
  }

  return { dashboard, contactos, oportunidades, tareas, bot, toast };
})();
