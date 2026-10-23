const API_BASE_URL = window.location.protocol === "file:"
    ? "http://127.0.0.1:5000/api"
    : `${window.location.protocol}//${window.location.hostname}:5000/api`;
const token = new URLSearchParams(window.location.search).get("ref");
const form = document.getElementById("lead-form");
const message = document.getElementById("message");

if (!token) {
    form.style.display = "none";
    showMessage("Ce lien de formulaire est invalide.", "error");
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = document.getElementById("submit-btn");
    button.disabled = true;
    try {
        const response = await fetch(`${API_BASE_URL}/public/leads`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                token,
                first_name: document.getElementById("first_name").value.trim(),
                last_name: document.getElementById("last_name").value.trim(),
                phone: document.getElementById("phone").value.trim(),
                email: document.getElementById("email").value.trim(),
                study_level: document.getElementById("study_level").value,
                speciality: document.getElementById("speciality").value.trim(),
                desired_destination: document.getElementById("desired_destination").value.trim(),
                study_information: document.getElementById("study_information").value.trim(),
            }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.message || "Une erreur est survenue.");
        form.reset();
        form.style.display = "none";
        showMessage(data.message, "success");
    } catch (error) {
        showMessage(error.message, "error");
    } finally {
        button.disabled = false;
    }
});

function showMessage(text, type) {
    message.textContent = text;
    message.className = type;
}
