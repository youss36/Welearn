const API_BASE_URL = "http://127.0.0.1:5000/api";

document.addEventListener("DOMContentLoaded", () => {
    const loginBtn = document.getElementById("login-btn");
    const errorMsg = document.getElementById("error-msg");

    loginBtn.addEventListener("click", async () => {
        errorMsg.style.display = "none";

        const email = document.getElementById("email").value.trim();
        const password = document.getElementById("password").value;

        try {
            const response = await fetch(`${API_BASE_URL}/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });
            const data = await response.json();

            if (!response.ok || data.status !== "success") {
                throw new Error(data.message || "Connexion impossible.");
            }

            localStorage.setItem("user_id", data.user.id);
            localStorage.setItem("user_name", data.user.name);
            localStorage.setItem("user_role", data.user.role);
            localStorage.setItem("user_type", data.user.type);
            if (data.user.type === "agent") {
                window.location.href = "agent.html";
            } else if (data.user.type === "influencer") {
                window.location.href = "influencer.html";
            } else {
                window.location.href = "dashboard.html";
            }
        } catch (error) {
            errorMsg.innerText = error.message || "Serveur indisponible.";
            errorMsg.style.display = "block";
        }
    });
});
