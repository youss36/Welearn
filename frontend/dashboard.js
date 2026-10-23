const API_BASE_URL = "http://127.0.0.1:5000/api";
const destinations = ["Allemagne", "Turquie", "Hongrie", "Espagne", "Chine", "Malte", "Autre"];
const demoUniversities = [
    {
        id: "demo-1",
        name: "Technical University of Munich (TUM)",
        city: "Munich",
        country: "Allemagne",
        website: "https://www.tum.de",
        available_programs: "Software Engineering, Robotics, Biomedical Engineering, MBA",
        study_domain: "Informatique et Ingenierie",
        degree_level: "Master, MBA, Doctorat",
        teaching_language: "Anglais / Allemand",
        tuition_fee: 0,
        scholarships_available: true,
        guaranteed_admission: false,
        admission_conditions: "Excellent dossier academique, TOEFL iBT 88 ou IELTS 6.5 selon le programme.",
        required_documents: "Diplome, releves de notes, certificat de langue, CV, lettres de recommandation.",
        deadlines: "31 Mai 2026",
        internal_notes: "Universite tres demandee. Verifier les frais administratifs par semestre.",
    },
    {
        id: "demo-2",
        name: "Istanbul Technical University",
        city: "Istanbul",
        country: "Turquie",
        website: "https://www.itu.edu.tr",
        available_programs: "Engineering, Architecture, Computer Science, Management",
        study_domain: "Ingenierie",
        degree_level: "Licence, Master",
        teaching_language: "Anglais / Turc",
        tuition_fee: 2500,
        scholarships_available: true,
        guaranteed_admission: true,
        admission_conditions: "Dossier academique complet. Certains programmes demandent un test de langue.",
        required_documents: "Passeport, diplome, releves, photo, formulaire de candidature.",
        deadlines: "15 Juillet 2026",
        internal_notes: "Bonne option pour budget moyen et admission rapide.",
    },
    {
        id: "demo-3",
        name: "University of Szeged",
        city: "Szeged",
        country: "Hongrie",
        website: "https://u-szeged.hu",
        available_programs: "Medicine, Business, Computer Science, Humanities",
        study_domain: "Medecine et Business",
        degree_level: "Licence, Master, Doctorat",
        teaching_language: "Anglais",
        tuition_fee: 4200,
        scholarships_available: true,
        guaranteed_admission: false,
        admission_conditions: "Entretien possible selon le programme. Niveau anglais recommande.",
        required_documents: "Passeport, releves, diplome, CV, lettre de motivation.",
        deadlines: "30 Juin 2026",
        internal_notes: "Verifier les programmes de medecine separement.",
    },
];

let allUniversities = [];
let pipelineStatuses = [];
let pipelineLeads = {};
let pendingConfirmation = null;
let editingLeadId = null;

document.addEventListener("DOMContentLoaded", async () => {
    const userName = localStorage.getItem("user_name");
    const userRole = localStorage.getItem("user_role");

    if (!userName) {
        window.location.href = "index.html";
        return;
    }

    document.getElementById("user-name").innerText = userName;
    document.getElementById("user-role").innerText = userRole;
    document.getElementById("user-initial").innerText = userName.charAt(0).toUpperCase();
    document.getElementById("user-name-small").innerText = userName;
    document.getElementById("logout-btn").addEventListener("click", logout);
    document.getElementById("add-lead-btn").addEventListener("click", addLead);
    document.getElementById("toggle-uni-form-btn").addEventListener("click", toggleUniversityForm);
    document.getElementById("cancel-uni-form-btn").addEventListener("click", cancelUniversityForm);
    document.getElementById("add-uni-btn").addEventListener("click", addUniversity);
    document.getElementById("upload-doc-btn").addEventListener("click", uploadDocument);
    document.getElementById("toggle-inf-form-btn").addEventListener("click", toggleInfForm);
    document.getElementById("cancel-inf-btn").addEventListener("click", cancelInfForm);
    document.getElementById("save-inf-btn").addEventListener("click", saveInfluencer);
    document.getElementById("toggle-user-form-btn").addEventListener("click", toggleUserForm);
    document.getElementById("cancel-user-btn").addEventListener("click", cancelUserForm);
    document.getElementById("save-user-btn").addEventListener("click", saveUser);
    document.getElementById("save-profile-btn").addEventListener("click", saveProfile);
    document.getElementById("copy-account-link-btn").addEventListener("click", copyAccountLink);
    document.getElementById("download-account-qr-btn").addEventListener("click", downloadAccountQr);
    document.getElementById("user-badge-btn").addEventListener("click", () => {
        switchSection("profile-section", document.querySelector('.menu-btn[onclick*="profile-section"]'));
    });

    populateDestinationSelects();
    await loadPipelineStatuses();
    await loadDocTypes();
    populateDocTypes();
    await loadDocLeadSelect();
    if (userRole === "admin") {
        await loadInfluencers();
        await loadUsers();
        document.querySelectorAll(".admin-only").forEach((el) => el.style.display = "");
    }
    await Promise.all([loadDashboardKpis(), loadLeads(), loadUniversities(), loadAppointments()]);
    loadProfile();
    loadAccountLink();

    loadNotifCount();
    setInterval(loadNotifCount, 30000);
});

function logout() {
    localStorage.clear();
    window.location.href = "index.html";
}

async function loadAccountLink() {
    try {
        const data = await apiFetch("/account-link");
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
    } catch (err) {
        showError("Lien de formulaire: " + err.message);
    }
}

async function renderAccountQr(url) {
    const container = document.getElementById("account-qr");
    container.innerHTML = "";
    if (!window.QRCode) {
        container.textContent = "Generation du QR code indisponible.";
        return;
    }
    const canvas = document.createElement("canvas");
    await QRCode.toCanvas(canvas, url, { width: 220, margin: 2, errorCorrectionLevel: "H" });
    const context = canvas.getContext("2d");
    const logo = new Image();
    logo.crossOrigin = "anonymous";
    await new Promise((resolve) => { logo.onload = resolve; logo.onerror = resolve; logo.src = "logo.svg"; });
    if (logo.complete && logo.naturalWidth) {
        try {
            const logoSize = Math.round(canvas.width * 0.19);
            const position = (canvas.width - logoSize) / 2;
            context.fillStyle = "#ffffff";
            context.fillRect(position - 5, position - 5, logoSize + 10, logoSize + 10);
            context.drawImage(logo, position, position, logoSize, logoSize);
        } catch {}
    }
    container.append(canvas);
}

function downloadAccountQr() {
    const canvas = document.querySelector("#account-qr canvas");
    if (!canvas) {
        showError("QR code non genere.");
        return;
    }
    try {
        const link = document.createElement("a");
        link.download = "we-learn-formulaire-qr.png";
        link.href = canvas.toDataURL("image/png");
        document.body.appendChild(link);
        link.click();
        link.remove();
    } catch (e) {
        try {
            const url = document.getElementById("account-link").value;
            QRCode.toDataURL(url, { width: 600, margin: 2, errorCorrectionLevel: "H" }, (err, dataUrl) => {
                if (err || !dataUrl) throw err || new Error("QR");
                const link = document.createElement("a");
                link.download = "we-learn-formulaire-qr.png";
                link.href = dataUrl;
                document.body.appendChild(link);
                link.click();
                link.remove();
            });
        } catch (err2) {
            showError("Echec du telechargement: " + (e.message || "canvas tainted"));
        }
    }
}

async function copyAccountLink() {
    const input = document.getElementById("account-link");
    if (!input.value) return;
    await navigator.clipboard.writeText(input.value);
    alert("Lien copie.");
}

function switchSection(sectionId, clickedButton) {
    document.querySelectorAll(".app-section").forEach((section) => section.classList.remove("active"));
    document.getElementById(sectionId).classList.add("active");
    document.querySelectorAll(".menu-btn").forEach((button) => button.classList.remove("active"));
    clickedButton.classList.add("active");

    if (sectionId === "appointments-section") { loadAppointments(); }
    if (sectionId === "applications-section") {
        loadApplications();
        loadAppCounts();
        loadAppUniversities();
    }
}

function populateDestinationSelects() {
    const leadDestination = document.getElementById("lead-destination");
    const countryFilter = document.getElementById("filter-country");

    leadDestination.innerHTML = `<option value="">-- Choisir --</option>` + destinations.map((country) => `<option value="${country}">${country}</option>`).join("");
    document.getElementById("uni-country").innerHTML = destinations
        .map((country) => `<option value="${country}">${country}</option>`)
        .join("");
    countryFilter.innerHTML = `<option value="" selected>Pays: tout</option>${destinations
        .map((country) => `<option value="${country}">${country}</option>`)
        .join("")}`;
    countryFilter.value = "";

    document.getElementById("filter-language").innerHTML = `
        <option value="">Langue: tout</option>
        <option value="Anglais">Anglais</option>
        <option value="Allemand">Allemand</option>
        <option value="Turc">Turc</option>
        <option value="Espagnol">Espagnol</option>
        <option value="Francais">Francais</option>
    `;

    document.getElementById("filter-degree").innerHTML = `
        <option value="">Niveau: tout</option>
        <option value="Licence">Licence</option>
        <option value="Master">Master</option>
        <option value="MBA">MBA</option>
        <option value="Doctorat">Doctorat</option>
    `;
}

async function apiFetch(path, options = {}) {
    const headers = {
        ...(options.headers || {}),
        "X-User-Id": localStorage.getItem("user_id"),
        "X-User-Role": localStorage.getItem("user_role"),
    };
    let response;
    try {
        response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
    } catch {
        throw new Error("Impossible de contacter le serveur. Verifiez que le backend est en cours d execution.");
    }
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.message || "Erreur API.");
    }

    return data;
}

async function loadPipelineStatuses() {
    pipelineStatuses = await apiFetch("/pipeline-statuses");
}

async function loadDashboardKpis() {
    try {
        const kpis = await apiFetch("/dashboard/kpis");
        document.getElementById("kpi-total").innerText = kpis.total_leads || 0;
        document.getElementById("kpi-admissions").innerText = kpis.admissions_obtenues || 0;
        document.getElementById("kpi-visas").innerText = kpis.visas_obtenus || 0;
        document.getElementById("kpi-departs").innerText = kpis.departs_confirmes || 0;
        document.getElementById("kpi-conversion").innerText = `${kpis.taux_conversion || 0}%`;
    } catch (err) {
        showError("KPIs: " + err.message);
    }
}

async function addLead() {
    const payload = {
        full_name: document.getElementById("lead-full-name").value.trim(),
        phone: document.getElementById("lead-phone").value.trim(),
        whatsapp: document.getElementById("lead-whatsapp").value.trim(),
        email: document.getElementById("lead-email").value.trim(),
        study_level: document.getElementById("lead-study-level").value.trim(),
        average_score: document.getElementById("lead-average").value.trim(),
        budget: document.getElementById("lead-budget").value,
        desired_destination: document.getElementById("lead-destination").value,
        speciality: document.getElementById("lead-speciality").value.trim(),
        source: document.getElementById("lead-source").value.trim(),
        estimated_revenue: document.getElementById("lead-revenue").value,
        internal_notes: document.getElementById("lead-notes").value.trim(),
        changed_by_user_id: localStorage.getItem("user_id"),
    };

    if (!payload.full_name) {
        alert("Le nom complet est obligatoire.");
        return;
    }

    await apiFetch("/leads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    document.querySelectorAll("#lead-form input, #lead-form select, #lead-form textarea").forEach((field) => {
        field.value = "";
    });
    await Promise.all([loadDashboardKpis(), loadLeads()]);
    alert("Lead enregistre avec succes.");
}

async function loadLeads() {
    try {
        const leads = await apiFetch("/leads");
        const list = document.getElementById("leads-list");

        if (!leads.length) {
            list.innerHTML = `<tr><td colspan="7">Aucun lead pour le moment.</td></tr>`;
            return;
        }

        pipelineLeads = Object.fromEntries(leads.map((lead) => [lead.id, lead]));
        list.innerHTML = leads
            .map((lead) => {
                const options = pipelineStatuses
                    .map((status) => `<option value="${status}" ${lead.status === status ? "selected" : ""}>${status}</option>`)
                    .join("");

                return `
                    <tr>
                        <td><strong>${escapeHtml(lead.full_name)}</strong><br>${formatDate(lead.created_at)}</td>
                        <td>${escapeHtml(lead.phone || "-")}<br>${escapeHtml(lead.email || "-")}</td>
                        <td>${escapeHtml(lead.desired_destination || "-")}<br>${escapeHtml(lead.speciality || "-")}</td>
                        <td>${escapeHtml(lead.source || "-")}</td>
                        <td>${escapeHtml(lead.conseiller_name || "-")}</td>
                        <td><select onchange="updateStatus(${lead.id}, this.value)">${options}</select></td>
                        <td><button class="danger-btn" type="button" onclick="editLead(${lead.id})">Modifier</button> <button class="danger-btn" type="button" onclick="deleteLead(${lead.id})">Supprimer</button></td>
                    </tr>
                `;
            })
            .join("");
    } catch (err) {
        showError("Leads: " + err.message);
    }
}

async function editLead(leadId) {
    const lead = pipelineLeads[leadId];
    if (!lead) return;
    editingLeadId = leadId;
    document.getElementById("edit-lead-full-name").value = lead.full_name || "";
    document.getElementById("edit-lead-phone").value = lead.phone || "";
    document.getElementById("edit-lead-email").value = lead.email || "";
    document.getElementById("edit-lead-study-level").value = lead.study_level || "";
    document.getElementById("edit-lead-destination").value = lead.desired_destination || "";
    document.getElementById("edit-lead-speciality").value = lead.speciality || "";
    document.getElementById("edit-lead-source").value = lead.source || "";
    document.getElementById("edit-lead-notes").value = lead.internal_notes || "";
    document.getElementById("lead-edit-modal").style.display = "flex";
}

function closeLeadEditModal() {
    editingLeadId = null;
    document.getElementById("lead-edit-modal").style.display = "none";
}

async function saveLeadEdit() {
    if (!editingLeadId) return;
    const payload = {
        full_name: document.getElementById("edit-lead-full-name").value.trim(),
        phone: document.getElementById("edit-lead-phone").value.trim(),
        email: document.getElementById("edit-lead-email").value.trim(),
        study_level: document.getElementById("edit-lead-study-level").value.trim(),
        desired_destination: document.getElementById("edit-lead-destination").value.trim(),
        speciality: document.getElementById("edit-lead-speciality").value.trim(),
        source: document.getElementById("edit-lead-source").value.trim(),
        internal_notes: document.getElementById("edit-lead-notes").value.trim(),
    };
    if (!payload.full_name) {
        showError("Le nom complet est obligatoire.");
        return;
    }
    await apiFetch(`/leads/${editingLeadId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    closeLeadEditModal();
    await loadLeads();
    showSuccess("Lead mis a jour avec succes.");
}

async function deleteLead(leadId) {
    openConfirmModal("Supprimer ce lead ?", "Cette action supprimera definitivement le lead, ses documents et son historique.", "Supprimer", true, async () => {
        await apiFetch(`/leads/${leadId}`, { method: "DELETE" });
        await Promise.all([loadDashboardKpis(), loadLeads(), loadDocLeadSelect()]);
        showSuccess("Lead supprime avec succes.");
    });
}

let pendingStatusLeadId = null;
let pendingStatusValue = null;
async function updateStatus(leadId, newStatus) {
    pendingStatusLeadId = leadId;
    pendingStatusValue = newStatus;
    const emailStatuses = ["Admission obtenue", "Paiement effectue", "Visa obtenu", "Depart confirme"];
    document.getElementById("status-action-title").textContent = "Changer le statut";
    document.getElementById("status-action-message").textContent = `Confirmez le passage du lead au statut "${newStatus}".`;
    document.getElementById("status-send-email").checked = emailStatuses.includes(newStatus);
    document.getElementById("status-send-whatsapp").checked = false;
    document.getElementById("status-action-modal").style.display = "flex";
}
function closeStatusActionModal() {
    document.getElementById("status-action-modal").style.display = "none";
    const id = pendingStatusLeadId;
    pendingStatusLeadId = null; pendingStatusValue = null;
    if (id) loadLeads();
}
async function confirmStatusAction() {
    const leadId = pendingStatusLeadId;
    const newStatus = pendingStatusValue;
    const sendEmail = document.getElementById("status-send-email").checked;
    const sendWhatsApp = document.getElementById("status-send-whatsapp").checked;
    document.getElementById("status-action-modal").style.display = "none";
    pendingStatusLeadId = null; pendingStatusValue = null;
    await applyStatus(leadId, newStatus, sendEmail, sendWhatsApp);
}
async function applyStatus(leadId, newStatus, sendEmail = false, sendWhatsApp = false) {
    await apiFetch(`/leads/${leadId}/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            status: newStatus,
            changed_by_user_id: localStorage.getItem("user_id"),
            send_email: sendEmail,
        }),
    });
    if (sendWhatsApp) {
        const lead = pipelineLeads[leadId];
        const phone = (lead?.phone || lead?.whatsapp || "").replace(/[^0-9]/g, "");
        if (phone) {
            const msg = `Bonjour ${lead.full_name||""},\nVotre dossier We Learn est passe au statut: *${newStatus}*.${lead.desired_destination ? `\nDestination: ${lead.desired_destination}` : ""}\nMerci pour votre confiance.`;
            window.open(`https://wa.me/${phone}?text=${encodeURIComponent(msg)}`, "_blank");
        } else {
            showError("WhatsApp non envoye: numero manquant.");
        }
    }
    await Promise.all([loadDashboardKpis(), loadLeads()]);
    showSuccess("Statut mis a jour avec succes." + (sendEmail ? " Email envoye." : "") + (sendWhatsApp ? " WhatsApp ouvert." : ""));
}

function openConfirmModal(title, text, confirmText, isDangerous, action, onCancel = null) {
    pendingConfirmation = { action, onCancel };
    document.getElementById("confirm-modal-title").textContent = title;
    document.getElementById("confirm-modal-message").textContent = text;
    const button = document.getElementById("confirm-modal-submit");
    button.textContent = confirmText;
    button.className = isDangerous ? "danger-btn" : "form-btn";
    button.onclick = async () => {
        const confirmation = pendingConfirmation;
        closeConfirmModal(false);
        if (confirmation?.action) await confirmation.action();
    };
    document.getElementById("confirm-modal").style.display = "flex";
}

function closeConfirmModal(runCancelAction = true) {
    const cancelAction = pendingConfirmation?.onCancel;
    pendingConfirmation = null;
    document.getElementById("confirm-modal").style.display = "none";
    if (runCancelAction && cancelAction) cancelAction();
}

async function loadUniversities() {
    try {
        const universities = await apiFetch("/universities");
        allUniversities = universities.length ? universities : demoUniversities;
    } catch (err) {
        showError("Universites: " + err.message + " (affichage des donnees de demonstration)");
        allUniversities = demoUniversities;
    }
    document.getElementById("filter-country").value = "";
    displayUniversities(allUniversities);
}

function toggleUniversityForm() {
    document.getElementById("uni-form").classList.toggle("active");
}

function cancelUniversityForm() {
    clearUniversityForm();
    document.getElementById("uni-form").classList.remove("active");
}

async function addUniversity() {
    const payload = {
        name: document.getElementById("uni-name").value.trim(),
        city: document.getElementById("uni-city").value.trim(),
        country: document.getElementById("uni-country").value,
        website: document.getElementById("uni-website").value.trim(),
        available_programs: document.getElementById("uni-programs").value.trim(),
        study_domain: document.getElementById("uni-domain").value.trim(),
        degree_level: document.getElementById("uni-degree").value.trim(),
        teaching_language: document.getElementById("uni-language").value.trim(),
        tuition_fee: document.getElementById("uni-fee").value || 0,
        scholarships_available: document.getElementById("uni-scholarship").checked,
        guaranteed_admission: document.getElementById("uni-guaranteed").checked,
        admission_conditions: document.getElementById("uni-conditions").value.trim(),
        required_documents: document.getElementById("uni-documents").value.trim(),
        deadlines: document.getElementById("uni-deadlines").value.trim(),
        internal_notes: document.getElementById("uni-notes").value.trim(),
    };

    if (!payload.name || !payload.city || !payload.country) {
        alert("Nom, ville et pays sont obligatoires.");
        return;
    }

    await apiFetch("/universities", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    clearUniversityForm();
    document.getElementById("uni-form").classList.remove("active");
    await loadUniversities();
    alert("Universite ajoutee dans la base de donnees.");
}

async function deleteUniversity(universityId) {
    if (!confirm("Supprimer cette universite de la base de donnees ?")) {
        return;
    }

    await apiFetch(`/universities/${universityId}`, { method: "DELETE" });
    await loadUniversities();
    alert("Universite supprimee.");
}

function clearUniversityForm() {
    document.querySelectorAll("#uni-form input, #uni-form textarea").forEach((field) => {
        if (field.type === "checkbox") {
            field.checked = false;
        } else {
            field.value = "";
        }
    });
    document.getElementById("uni-country").value = destinations[0];
}

function filterUniversities() {
    const query = document.getElementById("search-uni").value.toLowerCase();
    const country = document.getElementById("filter-country").value;
    const language = document.getElementById("filter-language").value.toLowerCase();
    const degree = document.getElementById("filter-degree").value.toLowerCase();
    const scholarship = document.getElementById("filter-scholarship").value;

    const filtered = allUniversities.filter((uni) => {
        const searchable = [
            uni.name,
            uni.city,
            uni.country,
            uni.available_programs,
            uni.study_domain,
        ].join(" ").toLowerCase();

        const matchesQuery = !query || searchable.includes(query);
        const matchesCountry = !country || normalizeText(uni.country) === normalizeText(country);
        const matchesLanguage = !language || (uni.teaching_language || "").toLowerCase().includes(language);
        const matchesDegree = !degree || (uni.degree_level || "").toLowerCase().includes(degree);
        const matchesScholarship = scholarship === "" || String(Boolean(uni.scholarships_available)) === scholarship;

        return matchesQuery && matchesCountry && matchesLanguage && matchesDegree && matchesScholarship;
    });

    displayUniversities(filtered);
}

function displayUniversities(universities) {
    const grid = document.getElementById("universities-grid");

    if (!universities.length) {
        grid.innerHTML = `<p>Aucune universite ne correspond aux criteres.</p>`;
        return;
    }

    const isAdmin = localStorage.getItem("user_role") === "admin";
    grid.innerHTML = universities
        .map((uni) => `
            <article class="uni-card">
                <div class="uni-card-logo">
                    ${uni.logo_url || uni.thumbnail_url ? `<img src="${escapeAttribute(uni.logo_url || uni.thumbnail_url)}" alt="" onerror="this.parentElement.style.display='none'">` : ""}
                </div>
                <div class="uni-card-main">
                    <h4>${escapeHtml(uni.name)}</h4>
                    <p><strong>Ville/Pays:</strong> ${escapeHtml(uni.city)}, ${escapeHtml(uni.country)}</p>
                    <span class="badge">${escapeHtml(uni.degree_level || "-")}</span>
                    ${uni.scholarships_available ? `<span class="badge">Bourse</span>` : ""}
                    ${uni.guaranteed_admission ? `<span class="badge">Admission garantie</span>` : ""}
                </div>
                <div class="uni-card-meta">
                    <p><strong>Langue:</strong> ${escapeHtml(uni.teaching_language || "-")}</p>
                    <p><strong>Frais:</strong> ${formatMoney(uni.tuition_fee)} / an</p>
                </div>
                <div class="uni-card-actions">
                    <button class="form-btn" type="button" onclick="window.location.href='university.html?id=${escapeAttribute(uni.id)}'">Voir details</button>
                    ${isAdmin ? `<button class="danger-btn" type="button" onclick="deleteUniversity('${escapeAttribute(uni.id)}')">- Supprimer</button>` : ""}
                </div>
            </article>
        `)
        .join("");
}

function openUniModalById(universityId) {
    const university = allUniversities.find((uni) => String(uni.id) === String(universityId));
    if (university) {
        openUniModal(university);
    }
}

function openUniModal(uni) {
    const modal = document.getElementById("uni-modal");
    const content = document.getElementById("modal-body-content");
    content.innerHTML = `
        <h3>${escapeHtml(uni.name)}</h3>
        <p><strong>Localisation:</strong> ${escapeHtml(uni.city)}, ${escapeHtml(uni.country)}</p>
        <p><strong>Site web:</strong> <a href="${escapeAttribute(uni.website || "#")}" target="_blank">${escapeHtml(uni.website || "-")}</a></p>
        <p><strong>Programmes:</strong><br>${escapeHtml(uni.available_programs || "-")}</p>
        <p><strong>Domaine:</strong> ${escapeHtml(uni.study_domain || "-")}</p>
        <p><strong>Niveau:</strong> ${escapeHtml(uni.degree_level || "-")}</p>
        <p><strong>Langue:</strong> ${escapeHtml(uni.teaching_language || "-")}</p>
        <p><strong>Frais:</strong> ${formatMoney(uni.tuition_fee)} / an</p>
        <p><strong>Conditions:</strong><br>${escapeHtml(uni.admission_conditions || "-")}</p>
        <p><strong>Documents requis:</strong><br>${escapeHtml(uni.required_documents || "-")}</p>
        <p><strong>Dates limites:</strong> ${escapeHtml(uni.deadlines || "-")}</p>
        <p><strong>Notes internes:</strong><br>${escapeHtml(uni.internal_notes || "-")}</p>
    `;
    modal.style.display = "flex";
}

function closeUniModal() {
    document.getElementById("uni-modal").style.display = "none";
}

window.onclick = (event) => {
    const modal = document.getElementById("uni-modal");
    if (event.target === modal) {
        modal.style.display = "none";
    }
};

function formatDate(value) {
    return value ? new Date(value).toLocaleDateString("fr-FR") : "-";
}

function formatMoney(value) {
    const amount = Number(value || 0);
    return amount === 0 ? "Gratuit" : `${amount.toLocaleString("fr-FR")} EUR`;
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function escapeAttribute(value) {
    return escapeHtml(value).replaceAll("`", "&#096;");
}

function normalizeText(value) {
    return String(value || "").trim().toLowerCase();
}

let docTypes = [];
let selectedLeadId = null;

async function loadDocTypes() {
    docTypes = await apiFetch("/document-types");
}

function populateDocTypes() {
    const sel = document.getElementById("doc-type");
    sel.innerHTML = docTypes.map((t) => `<option value="${t}">${t}</option>`).join("");
}

async function loadDocLeadSelect() {
    try {
        const leads = await apiFetch("/leads");
        const sel = document.getElementById("doc-lead-select");
        sel.innerHTML = `<option value="">-- Choisir un lead --</option>` + leads
            .map((l) => `<option value="${l.id}">${escapeHtml(l.full_name)}</option>`)
            .join("");
    } catch (err) {
        showError("Chargement des leads: " + err.message);
    }
}

async function onDocLeadChange() {
    const sel = document.getElementById("doc-lead-select");
    selectedLeadId = sel.value;
    const panel = document.getElementById("doc-panel");
    if (!selectedLeadId) {
        panel.style.display = "none";
        return;
    }
    panel.style.display = "block";
    await loadDocuments(selectedLeadId);
}

async function loadDocuments(leadId) {
    try {
        const docs = await apiFetch(`/leads/${leadId}/documents`);
        const tbody = document.getElementById("doc-list");
        if (!docs.length) {
            tbody.innerHTML = `<tr><td colspan="4">Aucun document pour ce lead.</td></tr>`;
            return;
        }
        tbody.innerHTML = docs
            .map((d) => `
                <tr>
                    <td><strong>${escapeHtml(d.file_name)}</strong></td>
                    <td><span class="badge">${escapeHtml(d.document_type)}</span></td>
                    <td>${formatDate(d.uploaded_at)}</td>
                    <td>
                        <button class="form-btn" style="padding:6px 12px;font-size:12px" onclick="downloadDoc(${d.id})">Telecharger</button>
                        <button class="danger-btn" style="padding:6px 12px;font-size:12px" onclick="deleteDoc(${d.id})">Supprimer</button>
                    </td>
                </tr>
            `)
            .join("");
    } catch (err) {
        showError("Documents: " + err.message);
    }
}

async function uploadDocument() {
    if (!selectedLeadId) return;
    const fileInput = document.getElementById("doc-file");
    const file = fileInput.files[0];
    if (!file) {
        alert("Veuillez selectionner un fichier.");
        return;
    }
    const formData = new FormData();
    formData.append("file", file);
    formData.append("document_type", document.getElementById("doc-type").value);
    formData.append("uploaded_by_user_id", localStorage.getItem("user_id"));

    try {
        const response = await fetch(`${API_BASE_URL}/leads/${selectedLeadId}/documents`, {
            method: "POST",
            headers: {
                "X-User-Id": localStorage.getItem("user_id"),
                "X-User-Role": localStorage.getItem("user_role"),
            },
            body: formData,
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.message || "Erreur upload.");
        fileInput.value = "";
        await loadDocuments(selectedLeadId);
        alert("Document uploade avec succes.");
    } catch (err) {
        showError("Upload: " + err.message);
    }
}

async function deleteDoc(docId) {
    if (!confirm("Supprimer ce document ?")) return;
    try {
        await apiFetch(`/documents/${docId}`, { method: "DELETE" });
        if (selectedLeadId) await loadDocuments(selectedLeadId);
    } catch (err) {
        showError("Suppression: " + err.message);
    }
}

function downloadDoc(docId) {
    window.open(`${API_BASE_URL}/documents/${docId}/download`, "_blank");
}

let editingInfId = null;

function toggleInfForm() {
    const form = document.getElementById("inf-form");
    form.style.display = form.style.display === "none" ? "block" : "none";
    if (form.style.display === "none") cancelInfForm();
}

function cancelInfForm() {
    document.getElementById("inf-form").style.display = "none";
    document.getElementById("inf-name-input").value = "";
    document.getElementById("inf-email-input").value = "";
    document.getElementById("inf-password-input").value = "";
    document.getElementById("inf-promo-input").value = "";
    document.getElementById("inf-rate-input").value = "";
    editingInfId = null;
    document.querySelector("#inf-form h3").innerText = "Nouvel influenceur";
    document.getElementById("save-inf-btn").innerText = "Enregistrer";
}

async function loadInfluencers() {
    try {
        const influencers = await apiFetch("/admin/influencers");
        const tbody = document.getElementById("inf-list");
        if (!influencers.length) {
            tbody.innerHTML = `<tr><td colspan="6">Aucun influenceur pour le moment.</td></tr>`;
            return;
        }
        tbody.innerHTML = influencers
            .map((inf) => `
                <tr>
                    <td><strong>${escapeHtml(inf.name)}</strong></td>
                    <td>${escapeHtml(inf.email)}</td>
                    <td><span class="badge gold" style="font-family:monospace;font-size:12px">${escapeHtml(inf.promo_code)}</span></td>
                    <td>${inf.commission_rate}%</td>
                    <td>${inf.is_active ? '<span style="color:#27ae60;font-weight:600">Oui</span>' : '<span style="color:#e74c3c;font-weight:600">Non</span>'}</td>
                    <td>
                        <button class="form-btn" style="padding:6px 12px;font-size:12px" onclick="editInfluencer(${inf.id})">Modifier</button>
                        <button class="danger-btn" style="padding:6px 12px;font-size:12px" onclick="deleteInfluencer(${inf.id})">Supprimer</button>
                    </td>
                </tr>
            `)
            .join("");
    } catch (err) {
        showError("Influenceurs: " + err.message);
    }
}

async function saveInfluencer() {
    const payload = {
        name: document.getElementById("inf-name-input").value.trim(),
        email: document.getElementById("inf-email-input").value.trim(),
        password: document.getElementById("inf-password-input").value.trim(),
        promo_code: document.getElementById("inf-promo-input").value.trim(),
        commission_rate: parseFloat(document.getElementById("inf-rate-input").value) || 0,
    };

    if (!payload.name || !payload.email || !payload.promo_code) {
        alert("Nom, email et code promo sont obligatoires.");
        return;
    }

    try {
        if (editingInfId) {
            if (!payload.password) delete payload.password;
            await apiFetch(`/admin/influencers/${editingInfId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
        } else {
            if (!payload.password) {
                alert("Le mot de passe est requis pour un nouvel influenceur.");
                return;
            }
            await apiFetch("/admin/influencers", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
        }
        cancelInfForm();
        await loadInfluencers();
        alert(editingInfId ? "Influenceur modifie avec succes." : "Influenceur ajoute avec succes.");
    } catch (err) {
        showError(err.message);
    }
}

async function editInfluencer(id) {
    try {
        const influencers = await apiFetch("/admin/influencers");
        const inf = influencers.find((i) => i.id === id);
        if (!inf) return;
        document.getElementById("inf-name-input").value = inf.name;
        document.getElementById("inf-email-input").value = inf.email;
        document.getElementById("inf-password-input").value = "";
        document.getElementById("inf-promo-input").value = inf.promo_code;
        document.getElementById("inf-rate-input").value = inf.commission_rate;
        editingInfId = id;
        document.querySelector("#inf-form h3").innerText = "Modifier l'influenceur";
        document.getElementById("save-inf-btn").innerText = "Modifier";
        document.getElementById("inf-form").style.display = "block";
        document.getElementById("inf-password-input").placeholder = "Laisser vide pour conserver";
    } catch (err) {
        showError(err.message);
    }
}

async function deleteInfluencer(id) {
    if (!confirm("Supprimer cet influenceur ?")) return;
    try {
        await apiFetch(`/admin/influencers/${id}`, { method: "DELETE" });
        await loadInfluencers();
        alert("Influenceur supprime.");
    } catch (err) {
        showError(err.message);
    }
}

let editingUserId = null;

function toggleUserForm() {
    const form = document.getElementById("user-form");
    form.style.display = form.style.display === "none" ? "block" : "none";
    if (form.style.display === "none") cancelUserForm();
}

function cancelUserForm() {
    document.getElementById("user-form").style.display = "none";
    document.getElementById("user-name-input").value = "";
    document.getElementById("user-email-input").value = "";
    document.getElementById("user-password-input").value = "";
    document.getElementById("user-role-input").value = "conseiller";
    editingUserId = null;
    document.getElementById("user-form-title").innerText = "Nouvel utilisateur";
    document.getElementById("save-user-btn").innerText = "Enregistrer";
}

async function loadUsers() {
    try {
        const users = await apiFetch("/admin/users");
        const tbody = document.getElementById("users-list");
        if (!users.length) {
            tbody.innerHTML = `<tr><td colspan="5">Aucun utilisateur pour le moment.</td></tr>`;
            return;
        }
        tbody.innerHTML = users
            .map((u) => `
                <tr>
                    <td><strong>${escapeHtml(u.name)}</strong></td>
                    <td>${escapeHtml(u.email)}</td>
                    <td><span class="badge ${u.role === 'admin' ? 'gold' : ''}">${escapeHtml(u.role)}</span></td>
                    <td>${u.is_active ? '<span style="color:#27ae60;font-weight:600">Oui</span>' : '<span style="color:#e74c3c;font-weight:600">Non</span>'}</td>
                    <td>
                        <button class="form-btn" style="padding:6px 12px;font-size:12px" onclick="editUser(${u.id})">Modifier</button>
                        <button class="danger-btn" style="padding:6px 12px;font-size:12px" onclick="deleteUser(${u.id})">Supprimer</button>
                    </td>
                </tr>
            `)
            .join("");
    } catch (err) {
        showError("Utilisateurs: " + err.message);
    }
}

async function saveUser() {
    const payload = {
        name: document.getElementById("user-name-input").value.trim(),
        email: document.getElementById("user-email-input").value.trim(),
        password: document.getElementById("user-password-input").value.trim(),
        role: document.getElementById("user-role-input").value,
    };

    if (!payload.name || !payload.email) {
        alert("Nom et email sont obligatoires.");
        return;
    }

    try {
        if (editingUserId) {
            if (!payload.password) delete payload.password;
            await apiFetch(`/admin/users/${editingUserId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
        } else {
            if (!payload.password) {
                alert("Le mot de passe est requis pour un nouvel utilisateur.");
                return;
            }
            await apiFetch("/admin/users", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
        }
        cancelUserForm();
        await loadUsers();
        alert(editingUserId ? "Utilisateur modifie avec succes." : "Utilisateur ajoute avec succes.");
    } catch (err) {
        showError(err.message);
    }
}

async function editUser(id) {
    try {
        const users = await apiFetch("/admin/users");
        const u = users.find((x) => x.id === id);
        if (!u) return;
        document.getElementById("user-name-input").value = u.name;
        document.getElementById("user-email-input").value = u.email;
        document.getElementById("user-password-input").value = "";
        document.getElementById("user-password-input").placeholder = "Laisser vide pour conserver";
        document.getElementById("user-role-input").value = u.role;
        editingUserId = id;
        document.getElementById("user-form-title").innerText = "Modifier l'utilisateur";
        document.getElementById("save-user-btn").innerText = "Modifier";
        document.getElementById("user-form").style.display = "block";
    } catch (err) {
        showError(err.message);
    }
}

async function deleteUser(id) {
    if (!confirm("Supprimer cet utilisateur ?")) return;
    try {
        await apiFetch(`/admin/users/${id}`, { method: "DELETE" });
        await loadUsers();
        alert("Utilisateur supprime.");
    } catch (err) {
        showError(err.message);
    }
}

let notifOpen = false;
document.addEventListener("click", (e) => {
    const wrapper = document.querySelector(".notif-wrapper");
    if (notifOpen && wrapper && !wrapper.contains(e.target)) {
        document.getElementById("notif-dropdown").classList.remove("open");
        notifOpen = false;
    }
});

function toggleNotifications() {
    const dd = document.getElementById("notif-dropdown");
    notifOpen = !notifOpen;
    dd.classList.toggle("open", notifOpen);
    if (notifOpen) loadNotifications();
}

async function loadNotifCount() {
    try {
        const data = await apiFetch("/notifications/unread-count");
        const badge = document.getElementById("notif-badge");
        if (data.count > 0) {
            badge.innerText = data.count > 99 ? "99+" : data.count;
            badge.classList.add("show");
        } else {
            badge.classList.remove("show");
        }
    } catch {}
}

async function loadNotifications() {
    try {
        const notifs = await apiFetch("/notifications");
        const list = document.getElementById("notif-list");
        if (!notifs.length) {
            list.innerHTML = `<div class="notif-empty">Aucune notification.</div>`;
            return;
        }
        list.innerHTML = notifs
            .map((n) => `
                <div class="notif-item ${n.is_read ? "" : "unread"}" onclick="markRead(${n.id})">
                    <div class="notif-title">${escapeHtml(n.title)}</div>
                    <div class="notif-msg">${escapeHtml(n.message || "")}</div>
                    <div class="notif-time">${formatDate(n.created_at)}</div>
                </div>
            `)
            .join("");
    } catch {}
}

async function markRead(id) {
    try {
        await apiFetch(`/notifications/${id}/read`, { method: "PUT" });
        await loadNotifCount();
        const items = document.querySelectorAll(".notif-item");
        items.forEach((el) => el.classList.remove("unread"));
    } catch {}
}

async function markAllRead() {
    try {
        await apiFetch("/notifications/read-all", { method: "PUT" });
        document.querySelectorAll(".notif-item").forEach((el) => el.classList.remove("unread"));
        await loadNotifCount();
    } catch {}
}

function showError(message) {
    const container = document.getElementById("error-container") || (() => {
        const div = document.createElement("div");
        div.id = "error-container";
        div.style.cssText = "position:fixed;top:0;left:0;right:0;background:#e74c3c;color:#fff;padding:12px 20px;text-align:center;font-size:14px;z-index:9999;cursor:pointer";
        div.addEventListener("click", () => div.remove());
        document.body.prepend(div);
        return div;
    })();
    container.innerHTML = `&#9888; ${escapeHtml(message)} (cliquer pour fermer)`;
}

function showSuccess(message) {
    const container = document.getElementById("success-container") || (() => {
        const div = document.createElement("div");
        div.id = "success-container";
        div.style.cssText = "position:fixed;top:18px;right:18px;background:#167a4b;color:#fff;padding:12px 18px;border-radius:8px;box-shadow:0 8px 22px rgba(9,36,58,.18);font-size:14px;z-index:9999;cursor:pointer";
        div.addEventListener("click", () => div.remove());
        document.body.append(div);
        return div;
    })();
    container.textContent = message;
    setTimeout(() => container.remove(), 3500);
}

async function loadProfile() {
    try {
        const data = await apiFetch("/profile");
        document.getElementById("profile-avatar").innerText = (data.name || "").charAt(0).toUpperCase();
        document.getElementById("profile-name-display").innerText = data.name || "";
        document.getElementById("profile-role-display").innerText = data.role || "";
        document.getElementById("profile-email-display").innerText = data.email || "";
        document.getElementById("profile-name-input").value = data.name || "";
    } catch {
        const userName = localStorage.getItem("user_name");
        document.getElementById("profile-avatar").innerText = userName.charAt(0).toUpperCase();
        document.getElementById("profile-name-display").innerText = userName;
        document.getElementById("profile-name-input").value = userName;
    }
}

async function saveProfile() {
    const password = document.getElementById("profile-password-input").value;
    const confirmPassword = document.getElementById("profile-confirm-password-input").value;

    if (password && password !== confirmPassword) {
        alert("Les mots de passe ne correspondent pas.");
        return;
    }

    const payload = {
        name: document.getElementById("profile-name-input").value.trim(),
    };

    if (password) {
        payload.password = password;
    }

    try {
        await apiFetch("/profile", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        localStorage.setItem("user_name", payload.name);
        document.getElementById("user-name").innerText = payload.name;
        document.getElementById("user-initial").innerText = payload.name.charAt(0).toUpperCase();
        document.getElementById("user-name-small").innerText = payload.name;
        document.getElementById("profile-name-display").innerText = payload.name;
        document.getElementById("profile-avatar").innerText = payload.name.charAt(0).toUpperCase();

        document.getElementById("profile-password-input").value = "";
        document.getElementById("profile-confirm-password-input").value = "";

        alert("Profil mis a jour avec succes.");
    } catch (err) {
        showError(err.message);
    }
}

const APP_STATUSES = [
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

let appAll = [];
let appFilter = "";

function appStatusLabel(key) {
    const s = APP_STATUSES.find((s) => s.key === key);
    return s ? s.label : key;
}

function appFormatDate(iso) {
    if (!iso) return "-";
    return new Date(iso).toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit", year: "numeric" });
}

function renderAppStatusBar(counts) {
    const bar = document.getElementById("app-status-bar");
    if (!bar) return;
    const total = counts.total || 0;
    let html = `<button class="app-status-btn ${appFilter === "" ? "active" : ""}" data-c="total" onclick="filterApplications('')">Total (${total})</button>`;
    APP_STATUSES.forEach((s) => {
        const cnt = counts[s.key] || 0;
        if (cnt > 0) {
            html += `<button class="app-status-btn ${appFilter === s.key ? "active" : ""}" data-c="${s.color}" onclick="filterApplications('${s.key}')">${s.label} (${cnt})</button>`;
        }
    });
    bar.innerHTML = html;
}

function filterApplications(status) {
    appFilter = status;
    renderApplications();
    loadAppCounts();
}

function renderApplications() {
    const query = (document.getElementById("app-search")?.value || "").toLowerCase();
    const filtered = appAll.filter((a) => {
        if (appFilter && a.status !== appFilter) return false;
        if (query) {
            const haystack = [a.student_name, a.program_name, a.university_name, a.email].join(" ").toLowerCase();
            return haystack.includes(query);
        }
        return true;
    });

    document.getElementById("app-count").innerText = `${filtered.length} candidature${filtered.length !== 1 ? "s" : ""}`;

    const tbody = document.getElementById("app-tbody");
    if (!filtered.length) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;color:var(--text-muted);padding:40px">Aucune candidature trouvee.</td></tr>`;
        return;
    }

    tbody.innerHTML = filtered
        .map(
            (a) => `
        <tr>
            <td class="app-id">#${a.id}</td>
            <td class="app-student">${escapeHtml(a.student_name)}</td>
            <td>${escapeHtml(a.university_name || "-")}</td>
            <td>${escapeHtml(a.program_name || "-")}</td>
            <td>${escapeHtml(a.academic_year || "-")}</td>
            <td><span class="app-status-badge ${escapeHtml(a.status)}">${appStatusLabel(a.status)}</span></td>
            <td class="app-date">${appFormatDate(a.created_at)}</td>
            <td>
                <div class="app-actions">
                    <button class="app-icon-btn app-edit" onclick="editApplication(${a.id})" title="Modifier">&#9998;</button>
                    <button class="app-icon-btn app-del" onclick="deleteApplication(${a.id})" title="Supprimer">&#10005;</button>
                </div>
            </td>
        </tr>`
        )
        .join("");
}

async function loadAppCounts() {
    try {
        const counts = await apiFetch("/applications/status-counts");
        renderAppStatusBar(counts);
    } catch {}
}

async function loadApplications() {
    try {
        appAll = await apiFetch("/applications");
        renderApplications();
    } catch {
        document.getElementById("app-tbody").innerHTML = `<tr><td colspan="8" style="text-align:center;color:var(--text-muted);padding:40px">Erreur de chargement.</td></tr>`;
    }
}

function appPopulateStatus(selected) {
    const sel = document.getElementById("af-status");
    sel.innerHTML = APP_STATUSES.map(
        (s) => `<option value="${s.key}" ${s.key === selected ? "selected" : ""}>${s.label}</option>`
    ).join("");
}

function openAppModal(app) {
    document.getElementById("app-modal-title").innerText = app ? "Modifier la candidature" : "Nouvelle candidature";
    document.getElementById("af-id").value = app ? app.id : "";
    document.getElementById("af-student").value = app ? app.student_name : "";
    document.getElementById("af-email").value = app ? app.email || "" : "";
    document.getElementById("af-phone").value = app ? app.phone || "" : "";
    document.getElementById("af-whatsapp").value = app ? app.whatsapp || "" : "";
    document.getElementById("af-uni").value = app ? app.university_name || "" : "";
    document.getElementById("af-program").value = app ? app.program_name || "" : "";
    document.getElementById("af-year").value = app ? app.academic_year || "" : "";
    document.getElementById("af-notes").value = app ? app.internal_notes || "" : "";
    appPopulateStatus(app ? app.status : "pending_review");
    document.getElementById("app-modal").classList.add("open");
    document.getElementById("af-student").focus();
}

function closeAppModal() {
    document.getElementById("app-modal").classList.remove("open");
}

function editApplication(id) {
    const app = appAll.find((a) => a.id === id);
    if (app) openAppModal(app);
}

async function saveApplication() {
    const id = document.getElementById("af-id").value;
    const payload = {
        student_name: document.getElementById("af-student").value.trim(),
        email: document.getElementById("af-email").value.trim(),
        phone: document.getElementById("af-phone").value.trim(),
        whatsapp: document.getElementById("af-whatsapp").value.trim(),
        university_name: document.getElementById("af-uni").value.trim(),
        program_name: document.getElementById("af-program").value.trim(),
        academic_year: document.getElementById("af-year").value.trim(),
        status: document.getElementById("af-status").value,
        internal_notes: document.getElementById("af-notes").value.trim(),
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
        closeAppModal();
        loadApplications();
        loadAppCounts();
    } catch (e) {
        alert(e.message);
    }
}

async function deleteApplication(id) {
    if (!confirm("Supprimer cette candidature ?")) return;
    try {
        await apiFetch(`/applications/${id}`, { method: "DELETE" });
        loadApplications();
        loadAppCounts();
    } catch (e) {
        alert(e.message);
    }
}

function loadAppUniversities() {
    if (!allUniversities.length) return;
    const dl = document.getElementById("app-uni-list");
    if (dl) dl.innerHTML = allUniversities.map((u) => `<option value="${escapeHtml(u.name)}">`).join("");
}

let editingAptId = null;
function openAppointmentModal(id = null) {
    editingAptId = id;
    document.getElementById("apt-modal-title").textContent = id ? "Modifier rendez-vous" : "Nouveau rendez-vous";
    const leads = pipelineLeads ? Object.values(pipelineLeads) : [];
    document.getElementById("apt-lead").innerHTML = '<option value="">-- Choisir lead --</option>' + leads.map((l) => `<option value="${l.id}">${escapeHtml(l.full_name)} - ${escapeHtml(l.phone || "")}</option>`).join("");
    if (id) {
        const apt = window._appointmentsCache?.find((a) => a.id === id);
        if (apt) {
            document.getElementById("apt-lead").value = apt.lead_id;
            document.getElementById("apt-title").value = apt.title || "";
            document.getElementById("apt-date").value = apt.appointment_date?.slice(0, 10) || "";
            document.getElementById("apt-time").value = (apt.appointment_time || "").slice(0, 5);
            document.getElementById("apt-duration").value = apt.duration_minutes || 60;
            document.getElementById("apt-type").value = apt.type || "présentiel";
            document.getElementById("apt-location").value = apt.location || "";
            document.getElementById("apt-status").value = apt.status || "prévu";
            document.getElementById("apt-notes").value = apt.notes || "";
        }
    } else {
        ["apt-title","apt-date","apt-time","apt-location","apt-notes"].forEach((k) => document.getElementById(k).value = "");
        document.getElementById("apt-duration").value = 60;
        document.getElementById("apt-type").value = "présentiel";
        document.getElementById("apt-status").value = "prévu";
    }
    document.getElementById("appointment-modal").style.display = "flex";
}
function closeAppointmentModal() { document.getElementById("appointment-modal").style.display = "none"; editingAptId = null; }
async function loadAppointments() {
    try {
        const params = new URLSearchParams();
        const d = document.getElementById("apt-filter-date")?.value;
        const s = document.getElementById("apt-filter-status")?.value;
        if (d) { params.set("date_from", d); params.set("date_to", d); }
        if (s) params.set("status", s);
        const query = params.toString() ? `?${params.toString()}` : "";
        const data = await apiFetch(`/appointments${query}`);
        window._appointmentsCache = data;
        const tbody = document.getElementById("appointments-list");
        if (!data.length) { tbody.innerHTML = '<tr><td colspan="5">Aucun rendez-vous.</td></tr>'; return; }
        tbody.innerHTML = data.map((a) => `
            <tr>
                <td><strong>${escapeHtml(a.appointment_date?.slice(0,10))} ${escapeHtml((a.appointment_time||"").slice(0,5))}</strong><br><small>${escapeHtml(a.title||"")}</small></td>
                <td>${escapeHtml(a.lead_name||"-")}<br><small>${escapeHtml(a.lead_phone||a.lead_whatsapp||"")}</small></td>
                <td>${escapeHtml(a.type)}<br><small>${escapeHtml(a.location||"-")} (${a.duration_minutes} min)</small></td>
                <td><span class="badge">${escapeHtml(a.status)}</span></td>
                <td style="display:flex;gap:6px;flex-wrap:wrap">
                    <button class="danger-btn" onclick="openAppointmentModal(${a.id})">Modifier</button>
                    <button class="danger-btn" onclick="deleteAppointment(${a.id})">Supprimer</button>
                    <button class="form-btn" onclick="sendWhatsApp(${a.id})" style="background:#25D366">WhatsApp</button>
                    <button class="form-btn" onclick="sendEmail(${a.id})" style="background:#0a6b78">Email</button>
                </td>
            </tr>`).join("");
    } catch (e) { showError(e.message); }
}
async function saveAppointment() {
    const payload = {
        lead_id: document.getElementById("apt-lead").value,
        title: document.getElementById("apt-title").value.trim(),
        appointment_date: document.getElementById("apt-date").value,
        appointment_time: document.getElementById("apt-time").value,
        duration_minutes: document.getElementById("apt-duration").value,
        type: document.getElementById("apt-type").value,
        location: document.getElementById("apt-location").value.trim(),
        status: document.getElementById("apt-status").value,
        notes: document.getElementById("apt-notes").value.trim(),
    };
    if (!payload.lead_id || !payload.appointment_date || !payload.appointment_time) { showError("Lead, date et heure requis."); return; }
    try {
        if (editingAptId) await apiFetch(`/appointments/${editingAptId}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
        else await apiFetch("/appointments", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
        closeAppointmentModal(); await loadAppointments(); showSuccess("Rendez-vous enregistre.");
    } catch (e) { showError(e.message); }
}
async function deleteAppointment(id) {
    openConfirmModal("Supprimer le rendez-vous ?", "Cette action est irreversible.", "Supprimer", true, async () => {
        await apiFetch(`/appointments/${id}`, { method: "DELETE" }); await loadAppointments(); showSuccess("Supprime.");
    });
}
function sendWhatsApp(id) {
    const apt = window._appointmentsCache?.find((a) => a.id === id);
    if (!apt) return;
    const phone = (apt.lead_phone || apt.lead_whatsapp || "").replace(/[^0-9]/g, "");
    if (!phone) { showError("Numero WhatsApp manquant."); return; }
    const date = apt.appointment_date?.slice(0,10);
    const time = (apt.appointment_time||"").slice(0,5);
    const notesPart = apt.notes ? `\nNotes: ${apt.notes}` : "";
    const msg = `Bonjour ${apt.lead_name||""},\nVotre rendez-vous ${apt.title||"We Learn"} est prevu le ${date} a ${time} (${apt.type})\nLieu: ${apt.location||"-"}${notesPart}\nMerci de confirmer votre presence. - We Learn Consulting`;
    window.open(`https://wa.me/${phone}?text=${encodeURIComponent(msg)}`, "_blank");
}
async function sendEmail(id) {
    if (!confirm("Envoyer l'invitation par email au lead ?")) return;
    try {
        const res = await apiFetch(`/appointments/${id}/email`, { method: "POST" });
        showSuccess(res.message || "Email envoye.");
    } catch (e) { showError(e.message); }
}
