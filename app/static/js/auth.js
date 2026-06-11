async function login() {
  const email    = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const errEl    = document.getElementById("error");
  errEl.style.display = "none";

  if (!email || !password) {
    errEl.textContent = "Please fill in all fields";
    errEl.style.display = "block";
    return;
  }

  try {
    const data = await api("POST", "/auth/login", { email, password });
    setAuth(data.access_token, data.role, data.username);
    redirectByRole(data.role);
  } catch (e) {
    errEl.textContent = e.message;
    errEl.style.display = "block";
  }
}

async function register() {
  const username = document.getElementById("username").value.trim();
  const email    = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const role     = document.getElementById("role").value;
  const errEl    = document.getElementById("error");
  const sucEl    = document.getElementById("success");
  errEl.style.display = "none";
  sucEl.style.display = "none";

  if (!username || !email || !password) {
    errEl.textContent = "Please fill in all fields";
    errEl.style.display = "block";
    return;
  }

  try {
    await api("POST", "/auth/register", { username, email, password, role });
    sucEl.textContent = "Account created! Redirecting to login...";
    sucEl.style.display = "block";
    setTimeout(() => window.location.href = "/", 1500);
  } catch (e) {
    errEl.textContent = e.message;
    errEl.style.display = "block";
  }
}

document.addEventListener("keydown", e => {
  if (e.key === "Enter") {
    if (document.getElementById("password")) login();
  }
});