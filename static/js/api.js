// Cliente HTTP de la API con token JWT.
const API = (() => {
  const TOKEN_KEY = "khipu_token";

  function token() { return localStorage.getItem(TOKEN_KEY); }

  async function request(metodo, ruta, cuerpo) {
    const opciones = {
      method: metodo,
      headers: { "Content-Type": "application/json" },
    };
    if (token()) opciones.headers.Authorization = `Bearer ${token()}`;
    if (cuerpo) opciones.body = JSON.stringify(cuerpo);

    const resp = await fetch(ruta, opciones);

    if (resp.status === 401) {
      // Token inválido/expirado: volver al login.
      localStorage.removeItem(TOKEN_KEY);
      window.location.href = "/";
      throw new Error("No autorizado");
    }
    if (!resp.ok) {
      let detalle = `Error HTTP ${resp.status}`;
      try {
        const err = await resp.json();
        detalle = typeof err.detail === "string"
          ? err.detail
          : Object.values(err.detail?.[0] || {})[0] || JSON.stringify(err.detail);
      } catch (_) { /* respuesta sin JSON */ }
      throw new Error(detalle);
    }
    if (resp.status === 204) return null;
    return resp.json();
  }

  return {
    token,
    login: (username, password) =>
      request("POST", "/auth/login", { username, password }),
    get: (ruta) => request("GET", ruta),
    post: (ruta, cuerpo) => request("POST", ruta, cuerpo),
    put: (ruta, cuerpo) => request("PUT", ruta, cuerpo),
    del: (ruta) => request("DELETE", ruta),
    logout() { localStorage.removeItem(TOKEN_KEY); window.location.href = "/"; },
  };
})();
