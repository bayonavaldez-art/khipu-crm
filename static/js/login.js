// Pantalla de inicio de sesión.
document.addEventListener("DOMContentLoaded", () => {
  if (API.token()) window.location.href = "/app";

  const form = document.getElementById("form-login");
  const error = document.getElementById("login-error");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    error.hidden = true;
    try {
      const resp = await API.login(
        document.getElementById("username").value.trim(),
        document.getElementById("password").value
      );
      localStorage.setItem("khipu_token", resp.access_token);
      localStorage.setItem("khipu_rol", resp.rol);
      localStorage.setItem("khipu_nombre", resp.full_name);
      window.location.href = "/app";
    } catch (err) {
      error.textContent = err.message || "Credenciales incorrectas";
      error.hidden = false;
    }
  });
});
