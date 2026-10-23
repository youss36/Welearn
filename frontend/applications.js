const API_BASE = "http://127.0.0.1:5000/api";

const STATUSES = [
    { key: "pending_review", label: "En revue", color: "gray" },
    { key: "awaiting_conditional_acceptance", label: "Att. acceptation", color: "teal" },
    { key: "conditional_acceptance", label: "Acceptation cond.", color: "blue" },
    { key: "awaiting_payment", label: "Att. paiement", color: "teal" },
    { key: "paid", label: "Paye", color: "blue" },
    { key: "awaiting_final_acceptance", label: "Att. acceptation finale", color: "teal" },
    { key: "final_acceptance", label: "Acceptation finale", color: "green" },
    { key: "awaiting_student_card", label: "Att. carte etudiant", color: "teal" },
    { key: "completed", label: "Termine", color: "green" },
    { key: "invalid", label: "Invalide", color: "red" },
    { key: "refused", label: "Refuse", color: "red" },
    { key: "refund_request", label: "Demande remboursement", color: "darkred" },
    { key: "refunded", label: "Rembourse", color: "darkred" },
];

let allApplications = [];
let currentFilter = "";
let universities = [];

async function apiFetch(path, options = {}) {
    const headers = {
        "X-User-Id": localStorage.getItem("user_id") || "",
        "X-User-Role": localStorage.getItem("user_role") || "",
        ...(options.headers || {}),
    };
    const response = await fetch(API_BASE + path, { ...options, headers });
    if (response.status === 401) {
        window.location.href = "index.html";
        throw new Error("Non autorise");
    }
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(data.message || "Erreur serveur");
    }
    return data;
}

function escapeHtml(v) {
    return String(v || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function formatDate(iso) {
    if (!iso) return "-";
    const d = new Date(iso);
    return d.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit", year: "numeric" });
}

function getStatusLabel(key) {
    const s = STATUSES.find((s) => s.key === key);
    return s ? s.label : key;
}

function renderStatusBar(counts) {
    const bar = document.getElementById("status-bar");
    const total = counts.total || 0;
    let html = `<button class="status-btn ${currentFilter === "" ? "active" : ""}" data-color="total" onclick="filterBy('')">Total (${total})</button>`;
    STATUSES.forEach((s) => {
        const cnt = counts[s.key] || 0;
        html += `<button class="status-btn ${currentFilter === s.key ? "active" : ""}" data-color="${s.color}" onclick="filterBy('${s.key}')">${s.label} (${cnt})</button>`;
    });
    bar.innerHTML = html;
}

function filterBy(status) {
    currentFilter = status;
    render();
    loadCounts();
}

function render() {
    const query = document.getElementById("search").value.toLowerCase();
    const filtered = allApplications.filter((a) => {
        if (currentFilter && a.status !== currentFilter) return false;
        if (query) {
            const haystack = [a.student_name, a.program_name, a.university_name, a.email].join(" ").toLowerCase();
            return haystack.includes(query);
        }
        return true;
    });

    document.getElementById("count").innerText = `${filtered.length} candidature${filtered.length !== 1 ? "s" : ""}`;

    const tbody = document.getElementById("tbody");
    if (!filtered.length) {
        tbody.innerHTML = `<tr><td colspan="8" class="empty">Aucune candidature trouvee.</td></tr>`;
        return;
    }

    tbody.innerHTML = filtered
        .map(
            (a) => `
        <tr>
            <td class="id-col">#${a.id}</td>
            <td class="student-name">${escapeHtml(a.student_name)}</td>
            <td>${escapeHtml(a.university_name || "-")}</td>
            <td>${escapeHtml(a.program_name || "-")}</td>
            <td>${escapeHtml(a.academic_year || "-")}</td>
            <td><span class="status-badge ${escapeHtml(a.status)}">${getStatusLabel(a.status)}</span></td>
            <td class="date">${formatDate(a.created_at)}</td>
            <td>
                <div class="actions">
                    <button class="icon-btn edit" onclick="editApp(${a.id})" title="Modifier">&#9998;</button>
                    <button class="icon-btn delete" onclick="deleteApp(${a.id})" title="Supprimer">&#10005;</button>
                </div>
            </td>
        </tr>`
        )
        .join("");
}

async function loadCounts() {
    try {
        const counts = await apiFetch("/applications/status-counts");
        renderStatusBar(counts);
    } catch (e) {}
}

async function loadApplications() {
    try {
        allApplications = await apiFetch("/applications");
        render();
    } catch (e) {
        document.getElementById("tbody").innerHTML = `<tr><td colspan="8" class="empty">Erreur de chargement.</td></tr>`;
    }
}

async function loadUniversities() {
    try {
        universities = await apiFetch("/universities");
        const dl = document.getElementById("uni-list");
        dl.innerHTML = universities.map((u) => `<option value="${escapeHtml(u.name)}">`).join("");
    } catch (e) {}
}

function populateStatusSelect(selected) {
    const sel = document.getElementById("form-status");
    sel.innerHTML = STATUSES.map(
        (s) => `<option value="${s.key}" ${s.key === selected ? "selected" : ""}>${s.label}</option>`
    ).join("");
}

function openModal(app) {
    document.getElementById("modal-title").innerText = app ? "Modifier la candidature" : "Nouvelle candidature";
    document.getElementById("form-id").value = app ? app.id : "";
    document.getElementById("form-student").value = app ? app.student_name : "";
    document.getElementById("form-email").value = app ? app.email || "" : "";
    document.getElementById("form-phone").value = app ? app.phone || "" : "";
    document.getElementById("form-whatsapp").value = app ? app.whatsapp || "" : "";
    document.getElementById("form-uni").value = app ? app.university_name || "" : "";
    document.getElementById("form-program").value = app ? app.program_name || "" : "";
    document.getElementById("form-year").value = app ? app.academic_year || "" : "";
    document.getElementById("form-notes").value = app ? app.internal_notes || "" : "";
    populateStatusSelect(app ? app.status : "pending_review");
    document.getElementById("modal").classList.add("open");
    document.getElementById("form-student").focus();
}

function closeModal() {
    document.getElementById("modal").classList.remove("open");
}

function editApp(id) {
    const app = allApplications.find((a) => a.id === id);
    if (app) openModal(app);
}

async function save() {
    const id = document.getElementById("form-id").value;
    const payload = {
        student_name: document.getElementById("form-student").value.trim(),
        email: document.getElementById("form-email").value.trim(),
        phone: document.getElementById("form-phone").value.trim(),
        whatsapp: document.getElementById("form-whatsapp").value.trim(),
        university_name: document.getElementById("form-uni").value.trim(),
        program_name: document.getElementById("form-program").value.trim(),
        academic_year: document.getElementById("form-year").value.trim(),
        status: document.getElementById("form-status").value,
        internal_notes: document.getElementById("form-notes").value.trim(),
    };

    if (!payload.student_name) {
        alert("Le nom de l'etudiant est requis.");
        return;
    }

    try {
        if (id) {
            await apiFetch(`/applications/${id}`, { method: "PUT", body: JSON.stringify(payload) });
        } else {
            await apiFetch("/applications", { method: "POST", body: JSON.stringify(payload) });
        }
        closeModal();
        loadApplications();
        loadCounts();
    } catch (e) {
        alert(e.message);
    }
}

async function deleteApp(id) {
    if (!confirm("Supprimer cette candidature ?")) return;
    try {
        await apiFetch(`/applications/${id}`, { method: "DELETE" });
        loadApplications();
        loadCounts();
    } catch (e) {
        alert(e.message);
    }
}

async function init() {
    await Promise.all([loadApplications(), loadCounts(), loadUniversities()]);
}

document.addEventListener("DOMContentLoaded", init);
