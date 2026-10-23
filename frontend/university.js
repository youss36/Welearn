const API_BASE = "http://127.0.0.1:5000/api";

let university = null;
let programs = [];

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

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function formatMoney(value) {
    const amount = Number(value || 0);
    return amount === 0 ? "Gratuit" : `${amount.toLocaleString("fr-FR")} EUR`;
}

function parsePrograms(raw) {
    if (!raw) return [];
    return String(raw)
        .split("\n")
        .map((line) => line.trim())
        .filter((line) => line.startsWith("-"))
        .map((line) => {
            const rest = line.replace(/^-\s*/, "");
            const feeMatch = rest.match(/-\s*([\d.]+)\s*\$\/an$/i);
            const fee = feeMatch ? Number(feeMatch[1]) : 0;
            let name = rest;
            let meta = "";
            if (feeMatch) {
                name = rest.slice(0, feeMatch.index).trim();
            }
            const metaMatch = name.match(/\(([^)]+)\)$/);
            if (metaMatch) {
                meta = metaMatch[1];
                name = name.slice(0, metaMatch.index).trim();
            }
            const parts = meta.split("|").map((p) => p.trim());
            return {
                name,
                degree: parts[0] || "",
                duration: parts[1] || "",
                language: parts[2] || "",
                fee,
            };
        });
}

function renderUni() {
    if (!university) return;
    document.title = `${university.name} - We Learn CRM`;
    document.getElementById("uni-name").innerText = university.name;

    const banner = document.getElementById("uni-banner");
    if (university.background_url) {
        banner.style.backgroundImage = `url("${escapeHtml(university.background_url)}")`;
    }

    const logoImg = document.getElementById("uni-logo");
    if (university.logo_url || university.thumbnail_url) {
        logoImg.src = university.logo_url || university.thumbnail_url;
        logoImg.onerror = () => { document.querySelector(".uni-logo-wrap").style.display = "none"; };
    } else {
        document.querySelector(".uni-logo-wrap").style.display = "none";
    }

    const subParts = [];
    if (university.city) subParts.push(university.city);
    if (university.district) subParts.push(university.district);
    if (university.country) subParts.push(university.country);
    const website = university.website
        ? ` &middot; <a href="${escapeHtml(university.website)}" target="_blank">${escapeHtml(university.website)}</a>`
        : "";
    document.getElementById("uni-sub").innerHTML = escapeHtml(subParts.join(", ")) + website;

    const badges = [];
    if (university.degree_level) badges.push(`<span class="badge gold">${escapeHtml(university.degree_level)}</span>`);
    if (university.teaching_language) badges.push(`<span class="badge">${escapeHtml(university.teaching_language)}</span>`);
    if (university.scholarships_available) badges.push(`<span class="badge gold">Bourses disponibles</span>`);
    if (university.guaranteed_admission) badges.push(`<span class="badge gold">Admission garantie</span>`);
    if (university.without_language_certificate) badges.push(`<span class="badge">Sans certificat de langue</span>`);
    document.getElementById("uni-badges").innerHTML = badges.join("");

    const descCard = document.getElementById("desc-card");
    if (university.description) {
        const safeHtml = String(university.description)
            .replace(/<script[\s\S]*?<\/script>/gi, "")
            .replace(/<iframe[\s\S]*?<\/iframe>/gi, "")
            .replace(/\son\w+="[^"]*"/gi, "");
        document.getElementById("uni-description").innerHTML = safeHtml;
        descCard.style.display = "";
    } else {
        descCard.style.display = "none";
    }

    const infoItems = [
        { label: "Frais de scolarite", value: formatMoney(university.tuition_fee) + " / an" },
        { label: "Domaine d'etudes", value: university.study_domain || "-" },
        { label: "Nombre de programmes", value: String(programs.length) },
        { label: "Conditions d'admission", value: university.admission_conditions || "-" },
        { label: "Documents requis", value: university.required_documents || "-" },
        { label: "Dates limites", value: university.deadlines || "-" },
    ];
    document.getElementById("uni-info").innerHTML = infoItems
        .map(
            (item) => `
                <div class="info-item">
                    <div class="label">${escapeHtml(item.label)}</div>
                    <div class="value">${escapeHtml(item.value)}</div>
                </div>
            `
        )
        .join("");

    if (university.internal_notes) {
        document.getElementById("uni-info").insertAdjacentHTML(
            "beforeend",
            `<div class="info-item" style="grid-column: 1 / -1">
                <div class="label">Notes internes</div>
                <div class="value">${escapeHtml(university.internal_notes)}</div>
            </div>`
        );
    }
}

function renderPrograms() {
    const query = document.getElementById("search-program").value.toLowerCase();
    const degree = document.getElementById("filter-degree").value;
    const lang = document.getElementById("filter-lang").value.toLowerCase();

    const filtered = programs.filter((p) => {
        const matchesQuery = !query || (p.name + " " + p.faculty + " " + p.duration).toLowerCase().includes(query);
        const matchesDegree = !degree || p.degree.toLowerCase().includes(degree.toLowerCase());
        const matchesLang = !lang || p.language.toLowerCase().includes(lang);
        return matchesQuery && matchesDegree && matchesLang;
    });

    document.getElementById("programs-count").innerText = `${filtered.length} programme${filtered.length > 1 ? "s" : ""}`;

    const body = document.getElementById("programs-body");
    if (!filtered.length) {
        body.innerHTML = `<tr><td colspan="5" class="empty">Aucun programme ne correspond aux criteres.</td></tr>`;
        return;
    }

    body.innerHTML = filtered
        .map(
            (p) => `
                <tr>
                    <td><strong>${escapeHtml(p.name)}</strong></td>
                    <td>${escapeHtml(p.degree || "-")}</td>
                    <td>${escapeHtml(p.duration || "-")}</td>
                    <td class="lang">${escapeHtml(p.language || "-")}</td>
                    <td class="fee">${p.fee ? `$${p.fee.toLocaleString("fr-FR")}` : "-"}</td>
                </tr>
            `
        )
        .join("");
}

function exportToPdf() {
    const search = document.getElementById("search-program");
    const degree = document.getElementById("filter-degree");
    const lang = document.getElementById("filter-lang");
    const prevSearch = search.value;
    const prevDegree = degree.value;
    const prevLang = lang.value;
    search.value = "";
    degree.value = "";
    lang.value = "";
    renderPrograms();
    setTimeout(() => {
        window.print();
        setTimeout(() => {
            search.value = prevSearch;
            degree.value = prevDegree;
            lang.value = prevLang;
            renderPrograms();
        }, 100);
    }, 100);
}

async function init() {
    const params = new URLSearchParams(window.location.search);
    const id = params.get("id");
    if (!id) {
        window.location.href = "dashboard.html";
        return;
    }
    try {
        university = await apiFetch(`/universities/${id}`);
        programs = parsePrograms(university.available_programs);
        renderUni();
        renderPrograms();
    } catch (err) {
        document.getElementById("uni-name").innerText = "Erreur";
        document.getElementById("uni-sub").innerText = err.message;
    }
}

document.addEventListener("DOMContentLoaded", init);
