// Navegación principal del panel CRM.
document.addEventListener("DOMContentLoaded", async () => {
  if (!API.token()) {
    window.location.href = "/";
    return;
  }

  // Datos del usuario autenticado (valida el token contra la API).
  let usuario;
  try {
    usuario = await API.get("/auth/me");
  } catch (_) {
    return; // api.js ya redirige al login si el token es inválido
  }

  document.getElementById("user-info").innerHTML =
    `<strong>${usuario.full_name}</strong><br>rol: ${usuario.rol}`;

  const VISTAS = {
    dashboard: Views.dashboard,
    contactos: Views.contactos,
    oportunidades: Views.oportunidades,
    tareas: Views.tareas,
    bot: Views.bot,
  };

  async function mostrar(vista) {
    document.querySelectorAll(".vista").forEach((s) => (s.hidden = true));
    document.querySelectorAll(".nav-btn").forEach((b) => b.classList.toggle("active", b.dataset.vista === vista));
    const seccion = document.getElementById(`vista-${vista}`);
    seccion.hidden = false;
    seccion.innerHTML = "<p>Cargando…</p>";
    try {
      await VISTAS[vista](seccion);
    } catch (err) {
      seccion.innerHTML = `<p class="error-msg">Error al cargar: ${err.message}</p>`;
    }
  }

  document.querySelectorAll(".nav-btn").forEach((b) =>
    b.addEventListener("click", () => mostrar(b.dataset.vista)));

  document.getElementById("btn-logout").addEventListener("click", () => API.logout());

  await mostrar("dashboard");
});
