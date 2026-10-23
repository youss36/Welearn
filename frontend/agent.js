const API_BASE_URL = "http://127.0.0.1:5000/api";

document.addEventListener("DOMContentLoaded", async () => {
    const userName = localStorage.getItem("user_name");
    const userType = localStorage.getItem("user_type");

    if (!userName || userType !== "agent") {
        window.location.href = "index.html";
        return;
    }

    document.getElementById("user-initial").innerText = userName.charAt(0).toUpperCase();
    document.getElementById("user-name-small").innerText = userName;
    document.getElementById("logout-btn").addEventListener("click", logout);
    document.getElementById("save-profile-btn").addEventListener("click", saveProfile);
    document.getElementById("copy-account-link-btn").addEventListener("click", copyAccountLink);
    document.getElementById("download-account-qr-btn").addEventListener("click", downloadAccountQr);
    document.getElementById("upload-doc-btn").addEventListener("click", uploadDocument);

    document.getElementById("agent-logo-file").addEventListener("change", (e) => {
        const label = e.target.parentElement.querySelector(".file-label");
        label.textContent = e.target.files[0] ? e.target.files[0].name : "Aucun fichier selectionne";
    });

    await loadProfile();
    await loadAccountLink();
    await loadDocuments();
});

function logout() {
    localStorage.clear();
    window.location.href = "index.html";
}

async function loadAccountLink() {
    const response = await fetch(`${API_BASE_URL}/account-link`, { headers: getHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || "Erreur chargement lien.");
    let url;
    if (window.location.protocol === "file:") {
        let frontendUrl = "http://192.168.0.3:5500";
        try {
            const ipData = await fetch(`${API_BASE_URL}/server-ip`).then((r) => r.json());
            if (ipData.frontend_url) frontendUrl = ipData.frontend_url;
        } catch {}
        url = `${frontendUrl}/lead-form.html?ref=${encodeURIComponent(data.token)}`;
    } else {
        const u = new URL("lead-form.html", window.location.href);
        u.searchParams.set("ref", data.token);
        url = u.href;
    }
    document.getElementById("account-link").value = url;
    await renderAccountQr(url);
}

async function renderAccountQr(url) {
    const container = document.getElementById("account-qr");
    if (!window.QRCode) return;
    const canvas = document.createElement("canvas");
    await QRCode.toCanvas(canvas, url, { width: 180, margin: 2, errorCorrectionLevel: "H" });
    const context = canvas.getContext("2d");
    const logo = new Image();
    logo.crossOrigin = "anonymous";
    await new Promise((resolve) => { logo.onload = resolve; logo.onerror = resolve; logo.src = "logo.svg"; });
    if (logo.complete && logo.naturalWidth) {
        try {
            const size = Math.round(canvas.width * 0.19);
            const position = (canvas.width - size) / 2;
            context.fillStyle = "#ffffff";
            context.fillRect(position - 5, position - 5, size + 10, size + 10);
            context.drawImage(logo, position, position, size, size);
        } catch {}
    }
    container.replaceChildren(canvas);
}

function downloadAccountQr() {
    const canvas = document.querySelector("#account-qr canvas");
    if (!canvas) {
        showToast("QR code non genere.", "error");
        return;
    }
    try {
        const link = document.createElement("a");
        link.download = "we-learn-formulaire-qr.png";
        link.href = canvas.toDataURL("image/png");
        document.body.appendChild(link);
        link.click();
        link.remove();
        return;
    } catch (e) {}
    try {
        const url = document.getElementById("account-link").value;
        QRCode.toDataURL(url, { width: 600, margin: 2, errorCorrectionLevel: "H" }, (err, dataUrl) => {
            if (err || !dataUrl) return;
            const link = document.createElement("a");
            link.download = "we-learn-formulaire-qr.png";
            link.href = dataUrl;
            document.body.appendChild(link);
            link.click();
            link.remove();
        });
    } catch {}
    link.click();
}

async function copyAccountLink() {
    const input = document.getElementById("account-link");
    await navigator.clipboard.writeText(input.value);
    showToast("Lien copie.");
}

function switchSection(sectionId, clickedButton) {
    document.querySelectorAll(".app-section").forEach((s) => s.classList.remove("active"));
    document.getElementById(sectionId).classList.add("active");
    document.querySelectorAll(".menu-btn").forEach((b) => b.classList.remove("active"));
    clickedButton.classList.add("active");
}

function showToast(message, type = "success") {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => {
        toast.classList.remove("show");
    }, 3000);
}

function getHeaders() {
    return {
        "X-User-Id": localStorage.getItem("user_id"),
        "X-User-Role": "agent",
        "Content-Type": "application/json",
    };
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

async function loadProfile() {
    const agentId = localStorage.getItem("user_id");
    try {
        const response = await fetch(`${API_BASE_URL}/agent/${agentId}/profile`, {
            headers: getHeaders(),
        });
        if (!response.ok) throw new Error("Erreur chargement profil.");
        const agent = await response.json();

        document.getElementById("profile-display-name").textContent = agent.name || "WE LEARN";
        document.getElementById("profile-display-email").textContent = agent.email || "-";
        document.getElementById("agent-name").value = agent.name || "";
        document.getElementById("agent-country").value = agent.country || "";
        document.getElementById("agent-address").value = agent.address || "";
        document.getElementById("agent-facebook").value = agent.facebook || "";
        document.getElementById("agent-website").value = agent.website || "";
        document.getElementById("agent-instagram").value = agent.instagram || "";
        document.getElementById("agent-snapchat").value = agent.snapchat || "";

        if (agent.logo) {
            document.getElementById("profile-logo").innerHTML = `<img src="${agent.logo}" alt="Logo">`;
        }
    } catch (err) {
        showToast(err.message, "error");
    }
}

async function saveProfile() {
    const agentId = localStorage.getItem("user_id");
    const password = document.getElementById("agent-password").value;
    const confirmPassword = document.getElementById("agent-confirm-password").value;

    if (password && password !== confirmPassword) {
        showToast("Les mots de passe ne correspondent pas.", "error");
        return;
    }

    const logoFile = document.getElementById("agent-logo-file").files[0];
    let logoUrl = undefined;

    if (logoFile) {
        const formData = new FormData();
        formData.append("file", logoFile);
        try {
            const uploadResp = await fetch(`${API_BASE_URL}/agent/${agentId}/upload-logo`, {
                method: "POST",
                headers: {
                    "X-User-Id": localStorage.getItem("user_id"),
                    "X-User-Role": "agent",
                },
                body: formData,
            });
            if (uploadResp.ok) {
                const uploadData = await uploadResp.json();
                logoUrl = uploadData.url;
            }
        } catch {}
    }

    const payload = {
        name: document.getElementById("agent-name").value.trim(),
        country: document.getElementById("agent-country").value.trim(),
        address: document.getElementById("agent-address").value.trim(),
        facebook: document.getElementById("agent-facebook").value.trim(),
        website: document.getElementById("agent-website").value.trim(),
        instagram: document.getElementById("agent-instagram").value.trim(),
        snapchat: document.getElementById("agent-snapchat").value.trim(),
    };

    if (password) {
        payload.password = password;
    }
    if (logoUrl) {
        payload.logo = logoUrl;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/agent/${agentId}/profile`, {
            method: "PUT",
            headers: getHeaders(),
            body: JSON.stringify(payload),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.message || "Erreur.");

        localStorage.setItem("user_name", payload.name);
        document.getElementById("user-initial").innerText = payload.name.charAt(0).toUpperCase();
        document.getElementById("user-name-small").innerText = payload.name;
        document.getElementById("profile-display-name").textContent = payload.name;

        document.getElementById("agent-password").value = "";
        document.getElementById("agent-confirm-password").value = "";

        showToast("Profil mis a jour avec succes.");
        await loadProfile();
    } catch (err) {
        showToast(err.message, "error");
    }
}

async function loadDocuments() {
    const agentId = localStorage.getItem("user_id");
    try {
        const response = await fetch(`${API_BASE_URL}/agent/${agentId}/documents`, {
            headers: getHeaders(),
        });
        const docs = await response.json();
        const container = document.getElementById("doc-list-container");

        if (!docs.length) {
            container.innerHTML = `<div class="doc-empty">No Data Yet</div>`;
            return;
        }

        container.innerHTML = `<div class="doc-list">${
            docs.map((d) => `
                <div class="doc-item">
                    <div>
                        <div class="doc-item-name">${escapeHtml(d.file_name)}</div>
                        <div class="doc-item-type">${escapeHtml(d.document_type)}</div>
                    </div>
                    <div class="doc-item-actions">
                        <button class="doc-btn-download" onclick="downloadDoc(${d.id})">Telecharger</button>
                        <button class="doc-btn-delete" onclick="deleteDoc(${d.id})">Supprimer</button>
                    </div>
                </div>
            `).join("")
        }</div>`;
    } catch (err) {
        document.getElementById("doc-list-container").innerHTML = `<div class="doc-empty">No Data Yet</div>`;
    }
}

async function uploadDocument() {
    const agentId = localStorage.getItem("user_id");
    const fileInput = document.getElementById("doc-file");
    const file = fileInput.files[0];
    if (!file) {
        showToast("Veuillez selectionner un fichier.", "error");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("document_type", document.getElementById("doc-type").value);

    try {
        const response = await fetch(`${API_BASE_URL}/agent/${agentId}/documents`, {
            method: "POST",
            headers: {
                "X-User-Id": localStorage.getItem("user_id"),
                "X-User-Role": "agent",
            },
            body: formData,
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.message || "Erreur upload.");

        fileInput.value = "";
        await loadDocuments();
        showToast("Document uploade avec succes.");
    } catch (err) {
        showToast(err.message, "error");
    }
}

async function deleteDoc(docId) {
    if (!confirm("Supprimer ce document ?")) return;
    try {
        const response = await fetch(`${API_BASE_URL}/agent/documents/${docId}`, {
            method: "DELETE",
            headers: getHeaders(),
        });
        if (!response.ok) throw new Error("Erreur suppression.");
        await loadDocuments();
        showToast("Document supprime.");
    } catch (err) {
        showToast(err.message, "error");
    }
}

function downloadDoc(docId) {
    window.open(`${API_BASE_URL}/agent/documents/${docId}/download`, "_blank");
}
