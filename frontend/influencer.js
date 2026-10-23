const API_BASE_URL = "http://127.0.0.1:5000/api";

let influencerId = null;

document.addEventListener("DOMContentLoaded", async () => {
    influencerId = localStorage.getItem("user_id");
    const userName = localStorage.getItem("user_name");
    const userType = localStorage.getItem("user_type");

    if (!influencerId || userType !== "influencer") {
        window.location.href = "index.html";
        return;
    }

    document.getElementById("logout-btn").addEventListener("click", logout);
    document.getElementById("copy-account-link-btn").addEventListener("click", copyAccountLink);
    document.getElementById("download-account-qr-btn").addEventListener("click", downloadAccountQr);
    await loadDashboard();
    await loadAccountLink();
    loadNotifCount();
    setInterval(loadNotifCount, 30000);
});

function logout() {
    localStorage.clear();
    window.location.href = "index.html";
}

async function loadAccountLink() {
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
    alert("Lien copie.");
}

function switchSection(sectionId, clickedButton) {
    document.querySelectorAll(".app-section").forEach((s) => s.classList.remove("active"));
    document.getElementById(sectionId).classList.add("active");
    document.querySelectorAll(".menu-btn").forEach((b) => b.classList.remove("active"));
    clickedButton.classList.add("active");
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
        throw new Error("Impossible de contacter le serveur.");
    }
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || "Erreur API.");
    return data;
}

async function loadDashboard() {
    try {
        const data = await apiFetch(`/influencer/${influencerId}/dashboard`);
        const p = data.profile;

        document.getElementById("inf-name").innerText = p.name;
        document.getElementById("inf-email").innerText = p.email;
        document.getElementById("inf-rate").innerText = `${p.commission_rate}%`;
        document.getElementById("inf-promo").innerText = p.promo_code;

        document.getElementById("kpi-leads").innerText = data.total_leads;
        document.getElementById("kpi-estime").innerText = `${data.commissions_estimees.toLocaleString("fr-FR")} EUR`;
        document.getElementById("kpi-valide").innerText = `${data.commissions_validees.toLocaleString("fr-FR")} EUR`;
        document.getElementById("kpi-paye").innerText = `${data.commissions_payees.toLocaleString("fr-FR")} EUR`;
    } catch (err) {
        showError("Erreur chargement: " + err.message);
    }

    await Promise.all([loadLeads(), loadCommissions()]);
}

async function loadLeads() {
    try {
        const leads = await apiFetch(`/influencer/${influencerId}/leads`);
        const tbody = document.getElementById("inf-leads-list");
        if (!leads.length) {
            tbody.innerHTML = `<tr><td colspan="5">Aucun lead parraine pour le moment.</td></tr>`;
            return;
        }
        tbody.innerHTML = leads
            .map(
                (l) => `
            <tr>
                <td><strong>${escapeHtml(l.full_name)}</strong></td>
                <td>${escapeHtml(l.phone || "-")}<br>${escapeHtml(l.email || "-")}</td>
                <td>${escapeHtml(l.desired_destination || "-")}<br>${escapeHtml(l.speciality || "-")}</td>
                <td><span class="badge" style="background:rgba(9,107,120,0.08);color:var(--teal)">${escapeHtml(l.status)}</span></td>
                <td>${formatDate(l.created_at)}</td>
            </tr>
        `
            )
            .join("");
    } catch (err) {
        showError("Leads: " + err.message);
    }
}

async function loadCommissions() {
    try {
        const commissions = await apiFetch(`/influencer/${influencerId}/commissions`);
        const tbody = document.getElementById("inf-commissions-list");
        if (!commissions.length) {
            tbody.innerHTML = `<tr><td colspan="5">Aucune commission pour le moment.</td></tr>`;
            return;
        }
        tbody.innerHTML = commissions
            .map(
                (c) => `
            <tr>
                <td>${escapeHtml(c.lead_name || "-")}</td>
                <td><strong>${Number(c.amount || 0).toLocaleString("fr-FR")} EUR</strong></td>
                <td><span class="badge ${escapeHtml(c.status)}">${escapeHtml(c.status)}</span></td>
                <td>${escapeHtml(c.payment_note || "-")}</td>
                <td>${formatDate(c.created_at)}</td>
            </tr>
        `
            )
            .join("");
    } catch (err) {
        showError("Commissions: " + err.message);
    }
}

function formatDate(value) {
    return value ? new Date(value).toLocaleDateString("fr-FR") : "-";
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
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
