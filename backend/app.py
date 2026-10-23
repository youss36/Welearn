import os
import uuid
import smtplib
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename

from functools import wraps

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import mysql.connector


FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)

try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(_env_path)
except ImportError:
    pass


PIPELINE_STATUSES = [
    "Nouveau lead",
    "Contacte",
    "Interesse",
    "Documents demandes",
    "Documents recus",
    "Universite selectionnee",
    "Candidature deposee",
    "Admission obtenue",
    "Paiement effectue",
    "Visa en cours",
    "Visa obtenu",
    "Depart confirme",
    "Dossier cloture",
]


MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
MAIL_FROM = os.environ.get("MAIL_FROM", MAIL_USERNAME)
MAIL_FROM_NAME = os.environ.get("MAIL_FROM_NAME", "We Learn CRM")


def send_email(to_addresses, subject, html_body):
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        app.logger.warning("send_email: MAIL_USERNAME or MAIL_PASSWORD not set")
        return False
    try:
        import re
        plain_text = re.sub(r"<[^>]+>", "", html_body.replace("&nbsp;", " "))
        plain_text = "\n".join(line.strip() for line in plain_text.splitlines() if line.strip())
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{MAIL_FROM_NAME} <{MAIL_FROM}>"
        msg["To"] = to_addresses[0] if len(to_addresses) == 1 else ", ".join(to_addresses)
        msg["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
        msg["Message-ID"] = f"<{uuid.uuid4()}@{MAIL_SERVER.replace('smtp.', '')}>"
        msg["Reply-To"] = MAIL_FROM
        msg["X-Mailer"] = "We Learn CRM"
        msg["Auto-Submitted"] = "auto-generated"
        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as server:
            server.starttls()
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.sendmail(MAIL_FROM, to_addresses, msg.as_string())
        app.logger.info(f"Email sent to {to_addresses}: {subject}")
        return True
    except Exception as e:
        app.logger.error(f"send_email failed: {e}")
        return False


EMAIL_TEMPLATES = {
    "nouveau_lead": """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body{{font-family:Inter,sans-serif;background:#f4f6f9;margin:0;padding:0}}
.container{{max-width:600px;margin:30px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08)}}
.header{{background:linear-gradient(135deg,rgb(9,107,120),rgb(0,55,60));padding:28px 32px;text-align:center}}
.header h1{{color:rgb(241,208,106);margin:0;font-size:22px}}
.body{{padding:32px}}
.footer{{background:#f8f9fa;padding:16px 32px;text-align:center;font-size:12px;color:#888}}
.badge{{display:inline-block;background:rgb(241,208,106);color:rgb(9,36,58);padding:4px 14px;border-radius:20px;font-size:13px;font-weight:600}}
.btn{{display:inline-block;background:rgb(212,175,55);color:#fff;text-decoration:none;padding:10px 24px;border-radius:6px;font-weight:600}}
table{{width:100%;border-collapse:collapse;margin:16px 0}}
td{{padding:8px 12px;border-bottom:1px solid #eee;font-size:14px}}
td:first-child{{font-weight:600;color:rgb(9,107,120);width:40%}}
</style></head><body>
<div class="container">
<div class="header"><h1>Nouveau lead</h1></div>
<div class="body">
<p style="color:rgb(9,36,58);font-size:16px">Un nouveau lead a ete cree :</p>
<table><tr><td>Nom</td><td>{full_name}</td></tr>
<tr><td>Telephone</td><td>{phone}</td></tr>
<tr><td>Email</td><td>{email}</td></tr>
<tr><td>Destination</td><td>{destination}</td></tr>
<tr><td>Specialite</td><td>{speciality}</td></tr>
<tr><td>Source</td><td>{source}</td></tr>
<tr><td>CA estime</td><td>{revenue} EUR</td></tr></table>
<a class="btn" href="{link}">Voir le dossier</a>
</div>
<div class="footer">We Learn CRM</div>
</div></body></html>""",
    "admission": """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body{{font-family:Inter,sans-serif;background:#f4f6f9;margin:0;padding:0}}
.container{{max-width:600px;margin:30px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08)}}
.header{{background:linear-gradient(135deg,rgb(9,107,120),rgb(0,55,60));padding:28px 32px;text-align:center}}
.header h1{{color:rgb(241,208,106);margin:0;font-size:22px}}
.body{{padding:32px}}
.footer{{background:#f8f9fa;padding:16px 32px;text-align:center;font-size:12px;color:#888}}
.btn{{display:inline-block;background:rgb(212,175,55);color:#fff;text-decoration:none;padding:10px 24px;border-radius:6px;font-weight:600}}
</style></head><body>
<div class="container">
<div class="header"><h1>Admission obtenue</h1></div>
<div class="body">
<p style="color:rgb(9,36,58);font-size:16px"><strong>{full_name}</strong> a obtenu son admission !</p>
<p style="font-size:14px;color:#555">L'etudiant est passe au statut <strong>Admission obtenue</strong>.</p>
<a class="btn" href="{link}">Voir le dossier</a>
</div>
<div class="footer">We Learn CRM</div>
</div></body></html>""",
    "paiement": """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body{{font-family:Inter,sans-serif;background:#f4f6f9;margin:0;padding:0}}
.container{{max-width:600px;margin:30px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08)}}
.header{{background:linear-gradient(135deg,rgb(9,107,120),rgb(0,55,60));padding:28px 32px;text-align:center}}
.header h1{{color:rgb(241,208,106);margin:0;font-size:22px}}
.body{{padding:32px}}
.footer{{background:#f8f9fa;padding:16px 32px;text-align:center;font-size:12px;color:#888}}
.btn{{display:inline-block;background:rgb(212,175,55);color:#fff;text-decoration:none;padding:10px 24px;border-radius:6px;font-weight:600}}
</style></head><body>
<div class="container">
<div class="header"><h1>Paiement valide</h1></div>
<div class="body">
<p style="color:rgb(9,36,58);font-size:16px"><strong>{full_name}</strong> a effectue son paiement.</p>
<p style="font-size:14px;color:#555">Le dossier avance dans le pipeline.</p>
<a class="btn" href="{link}">Voir le dossier</a>
</div>
<div class="footer">We Learn CRM</div>
</div></body></html>""",
    "visa": """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body{{font-family:Inter,sans-serif;background:#f4f6f9;margin:0;padding:0}}
.container{{max-width:600px;margin:30px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08)}}
.header{{background:linear-gradient(135deg,rgb(9,107,120),rgb(0,55,60));padding:28px 32px;text-align:center}}
.header h1{{color:rgb(241,208,106);margin:0;font-size:22px}}
.body{{padding:32px}}
.footer{{background:#f8f9fa;padding:16px 32px;text-align:center;font-size:12px;color:#888}}
.btn{{display:inline-block;background:rgb(212,175,55);color:#fff;text-decoration:none;padding:10px 24px;border-radius:6px;font-weight:600}}
</style></head><body>
<div class="container">
<div class="header"><h1>Visa obtenu</h1></div>
<div class="body">
<p style="color:rgb(9,36,58);font-size:16px"><strong>{full_name}</strong> a obtenu son visa !</p>
<p style="font-size:14px;color:#555">Felicitations pour cette etape importante.</p>
<a class="btn" href="{link}">Voir le dossier</a>
</div>
<div class="footer">We Learn CRM</div>
</div></body></html>""",
    "depart": """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body{{font-family:Inter,sans-serif;background:#f4f6f9;margin:0;padding:0}}
.container{{max-width:600px;margin:30px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08)}}
.header{{background:linear-gradient(135deg,rgb(9,107,120),rgb(0,55,60));padding:28px 32px;text-align:center}}
.header h1{{color:rgb(241,208,106);margin:0;font-size:22px}}
.body{{padding:32px}}
.footer{{background:#f8f9fa;padding:16px 32px;text-align:center;font-size:12px;color:#888}}
.btn{{display:inline-block;background:rgb(212,175,55);color:#fff;text-decoration:none;padding:10px 24px;border-radius:6px;font-weight:600}}
</style></head><body>
<div class="container">
<div class="header"><h1>Depart confirme</h1></div>
<div class="body">
<p style="color:rgb(9,36,58);font-size:16px"><strong>{full_name}</strong> a confirme son depart !</p>
<p style="font-size:14px;color:#555">Le dossier est complete. Bonne continuation !</p>
<a class="btn" href="{link}">Voir le dossier</a>
</div>
<div class="footer">We Learn CRM</div>
</div></body></html>""",
}


def get_db_connection():
    host = os.environ.get("DB_HOST", "localhost")
    user = os.environ.get("DB_USER", "root")
    password = os.environ.get("DB_PASSWORD", "")
    database = os.environ.get("DB_NAME", "welearn_crm")
    ports = [int(os.environ.get("DB_PORT", 0)) or 0, 3306, 3307]
    ports = [p for p in ports if p]
    last_err = None
    for port in dict.fromkeys(ports):
        try:
            return mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                port=port,
                database=database,
                charset="utf8mb4",
                collation="utf8mb4_unicode_ci",
                connection_timeout=3,
            )
        except Exception as e:
            last_err = e
            continue
    raise last_err


def require_role(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            role = request.headers.get("X-User-Role")
            user_id = request.headers.get("X-User-Id")
            if not role or not user_id:
                return jsonify({"message": "Authentification requise."}), 401
            if role not in allowed_roles:
                return jsonify({"message": "Acces refuse: droits insuffisants."}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


def ensure_users_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(120) NOT NULL,
            email VARCHAR(160) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            role ENUM('admin', 'conseiller') NOT NULL DEFAULT 'conseiller',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )


def json_ready(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()
    if isinstance(value, timedelta):
        total = int(value.total_seconds())
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
    if isinstance(value, Decimal):
        return float(value)
    return value


def rows_to_json(rows):
    return [{key: json_ready(value) for key, value in row.items()} for row in rows]


def normalize_lead_row(row):
    normalized = dict(row)
    normalized["full_name"] = row.get("full_name") or row.get("name") or ""
    normalized["whatsapp"] = row.get("whatsapp") or row.get("phone")
    normalized["study_level"] = row.get("study_level") or ""
    normalized["average_score"] = row.get("average_score") or ""
    normalized["budget"] = row.get("budget") or 0
    normalized["desired_destination"] = row.get("desired_destination") or ""
    normalized["speciality"] = row.get("speciality") or ""
    normalized["source"] = row.get("source") or ""
    normalized["estimated_revenue"] = row.get("estimated_revenue") or 0
    normalized["internal_notes"] = row.get("internal_notes") or ""
    normalized["conseiller_name"] = row.get("conseiller_name") or "-"
    normalized["influencer_name"] = row.get("influencer_name") or "-"
    return {key: json_ready(value) for key, value in normalized.items()}


def table_exists(cursor, table_name):
    cursor.execute("SHOW TABLES LIKE %s", (table_name,))
    return cursor.fetchone() is not None


def get_table_columns(cursor, table_name):
    if not table_exists(cursor, table_name):
        return set()
    cursor.execute(f"SHOW COLUMNS FROM {table_name}")
    return {row["Field"] for row in cursor.fetchall()}


def ensure_leads_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INT AUTO_INCREMENT PRIMARY KEY,
            full_name VARCHAR(160) NOT NULL,
            phone VARCHAR(60),
            whatsapp VARCHAR(60),
            email VARCHAR(160),
            study_level VARCHAR(120),
            average_score VARCHAR(60),
            budget DECIMAL(10,2),
            desired_destination VARCHAR(120),
            speciality VARCHAR(160),
            source VARCHAR(120),
            assigned_conseiller_id INT,
            influencer_id INT,
            status VARCHAR(80) NOT NULL DEFAULT 'Nouveau lead',
            estimated_revenue DECIMAL(10,2) DEFAULT 0,
            internal_notes TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )
    columns = get_table_columns(cursor, "leads")
    if "agent_id" not in columns:
        cursor.execute("ALTER TABLE leads ADD COLUMN agent_id INT NULL")


def ensure_public_token_column(cursor, table_name):
    columns = get_table_columns(cursor, table_name)
    if "public_token" not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN public_token VARCHAR(64) NULL")
    cursor.execute(f"SELECT id FROM {table_name} WHERE public_token IS NULL OR public_token = ''")
    for row in cursor.fetchall():
        cursor.execute(f"UPDATE {table_name} SET public_token = %s WHERE id = %s", (uuid.uuid4().hex, row["id"]))


def ensure_status_history_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS lead_status_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            lead_id INT NOT NULL,
            old_status VARCHAR(80),
            new_status VARCHAR(80) NOT NULL,
            changed_by_user_id INT,
            note TEXT,
            changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )


def ensure_universities_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS universities (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            city VARCHAR(120) NOT NULL,
            country VARCHAR(120) NOT NULL,
            website VARCHAR(255),
            available_programs TEXT,
            study_domain VARCHAR(160),
            degree_level VARCHAR(120),
            teaching_language VARCHAR(120),
            tuition_fee DECIMAL(10,2) DEFAULT 0,
            scholarships_available BOOLEAN NOT NULL DEFAULT FALSE,
            without_language_certificate BOOLEAN NOT NULL DEFAULT FALSE,
            guaranteed_admission BOOLEAN NOT NULL DEFAULT FALSE,
            admission_conditions TEXT,
            required_documents TEXT,
            deadlines VARCHAR(160),
            internal_notes TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )


def seed_universities_if_empty(cursor):
    cursor.execute("SELECT COUNT(*) AS total FROM universities")
    total = cursor.fetchone()["total"]
    if total:
        return

    cursor.executemany(
        """
        INSERT INTO universities (
            name, city, country, website, available_programs, study_domain,
            degree_level, teaching_language, tuition_fee, scholarships_available,
            guaranteed_admission, admission_conditions, required_documents,
            deadlines, internal_notes
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        [
            (
                "Technical University of Munich (TUM)",
                "Munich",
                "Allemagne",
                "https://www.tum.de",
                "Software Engineering, Robotics, Biomedical Engineering, MBA",
                "Informatique et Ingenierie",
                "Master, MBA, Doctorat",
                "Anglais / Allemand",
                0,
                True,
                False,
                "Excellent dossier academique, TOEFL iBT 88 ou IELTS 6.5 selon le programme.",
                "Diplome, releves de notes, certificat de langue, CV, lettres de recommandation.",
                "31 Mai 2026",
                "Universite tres demandee. Verifier les frais administratifs par semestre.",
            ),
            (
                "Istanbul Technical University",
                "Istanbul",
                "Turquie",
                "https://www.itu.edu.tr",
                "Engineering, Architecture, Computer Science, Management",
                "Ingenierie",
                "Licence, Master",
                "Anglais / Turc",
                2500,
                True,
                True,
                "Dossier academique complet. Certains programmes demandent un test de langue.",
                "Passeport, diplome, releves, photo, formulaire de candidature.",
                "15 Juillet 2026",
                "Bonne option pour budget moyen et admission rapide.",
            ),
            (
                "University of Szeged",
                "Szeged",
                "Hongrie",
                "https://u-szeged.hu",
                "Medicine, Business, Computer Science, Humanities",
                "Medecine et Business",
                "Licence, Master, Doctorat",
                "Anglais",
                4200,
                True,
                False,
                "Entretien possible selon le programme. Niveau anglais recommande.",
                "Passeport, releves, diplome, CV, lettre de motivation.",
                "30 Juin 2026",
                "Verifier les programmes de medecine separement.",
            ),
        ],
    )


UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "doc", "docx", "xls", "xlsx", "zip"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


DOCUMENT_TYPES = [
    "Passeport",
    "Diplome",
    "Releve de notes",
    "CV",
    "Lettre de motivation",
    "Certificat de langue",
    "Autre",
]


def ensure_lead_documents_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS lead_documents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            lead_id INT NOT NULL,
            document_type VARCHAR(80) NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            uploaded_by_user_id INT,
            uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )


def ensure_commissions_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS commissions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            influencer_id INT NOT NULL,
            lead_id INT,
            status VARCHAR(20) NOT NULL DEFAULT 'estimee',
            amount DECIMAL(10,2) NOT NULL DEFAULT 0,
            payment_note TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            paid_at TIMESTAMP NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )


def ensure_notifications_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            target_type VARCHAR(20) NOT NULL,
            target_id INT,
            title VARCHAR(255) NOT NULL,
            message TEXT,
            link VARCHAR(500),
            is_read BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )


def notify_admins(cursor, title, message, link=None):
    ensure_notifications_table(cursor)
    cursor.execute("SELECT id FROM users WHERE role = 'admin' AND is_active = TRUE")
    for row in cursor.fetchall():
        cursor.execute(
            "INSERT INTO notifications (target_type, target_id, title, message, link) VALUES (%s, %s, %s, %s, %s)",
            ("admin", row["id"], title, message, link),
        )


def notify_user(cursor, target_type, target_id, title, message, link=None):
    ensure_notifications_table(cursor)
    cursor.execute(
        "INSERT INTO notifications (target_type, target_id, title, message, link) VALUES (%s, %s, %s, %s, %s)",
        (target_type, target_id, title, message, link),
    )


def get_request_data():
    return request.get_json(silent=True) or {}


def get_lan_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip.startswith("127."):
            raise ValueError
        return ip
    except Exception:
        return "192.168.0.3"


@app.route("/api/server-ip", methods=["GET"])
def server_ip():
    ip = get_lan_ip()
    return jsonify({"ip": ip, "frontend_url": f"http://{ip}:5000", "frontend_url_alt": f"http://{ip}:5500"})


@app.route("/lead-form.html")
def serve_lead_form():
    return send_from_directory(FRONTEND_DIR, "lead-form.html")


@app.route("/lead-form.js")
def serve_lead_form_js():
    return send_from_directory(FRONTEND_DIR, "lead-form.js")


@app.route("/qrcode-local.js")
def serve_qrcode_local():
    return send_from_directory(FRONTEND_DIR, "qrcode-local.js")


@app.route("/logo.svg")
def serve_logo():
    return send_from_directory(FRONTEND_DIR, "logo.svg")


@app.route("/<path:path>")
def serve_frontend_generic(path):
    if path.startswith("api/"):
        return jsonify({"message": "Not found"}), 404
    full_path = os.path.join(FRONTEND_DIR, path)
    if os.path.isfile(full_path):
        return send_from_directory(FRONTEND_DIR, path)
    return jsonify({"message": "Not found"}), 404


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/login", methods=["POST"])
def login():
    data = get_request_data()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"status": "error", "message": "Email et mot de passe requis."}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id, name, email, password, role FROM users WHERE email = %s AND is_active = TRUE",
        (email,),
    )
    user = cursor.fetchone()
    user_type = "user"

    if not user:
        cursor.execute(
            """
            SELECT id, name, email, password, 'influencer' AS role
            FROM influencers
            WHERE email = %s AND is_active = TRUE
            """,
            (email,),
        )
        user = cursor.fetchone()
        user_type = "influencer"

    if not user:
        ensure_agents_table(cursor)
        seed_agent_if_empty(cursor)
        conn.commit()
        cursor.execute(
            "SELECT id, name, email, password, 'agent' AS role FROM agents WHERE email = %s AND is_active = TRUE",
            (email,),
        )
        user = cursor.fetchone()
        user_type = "agent"

    cursor.close()
    conn.close()

    if user and user["password"] == password:
        user.pop("password", None)
        user["type"] = user_type
        return jsonify({"status": "success", "user": user}), 200

    return jsonify({"status": "error", "message": "Email ou mot de passe incorrect."}), 401


@app.route("/api/universities", methods=["GET"])
@require_role("admin", "conseiller")
def get_universities():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_universities_table(cursor)
    seed_universities_if_empty(cursor)
    conn.commit()
    cursor.execute("SELECT * FROM universities ORDER BY country, city, name")
    universities = rows_to_json(cursor.fetchall())
    cursor.close()
    conn.close()
    return jsonify(universities)


@app.route("/api/universities", methods=["POST"])
@require_role("admin")
def add_university():
    data = get_request_data()
    required_fields = ["name", "city", "country"]

    if any(not data.get(field) for field in required_fields):
        return jsonify({"message": "Nom, ville et pays sont requis."}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_universities_table(cursor)
    cursor.execute(
        """
        INSERT INTO universities (
            name, city, country, website, available_programs, study_domain,
            degree_level, teaching_language, tuition_fee, scholarships_available,
            without_language_certificate, guaranteed_admission, admission_conditions,
            required_documents, deadlines, internal_notes
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            data.get("name"),
            data.get("city"),
            data.get("country"),
            data.get("website"),
            data.get("available_programs"),
            data.get("study_domain"),
            data.get("degree_level"),
            data.get("teaching_language"),
            data.get("tuition_fee") or 0,
            bool(data.get("scholarships_available")),
            bool(data.get("without_language_certificate")),
            bool(data.get("guaranteed_admission")),
            data.get("admission_conditions"),
            data.get("required_documents"),
            data.get("deadlines"),
            data.get("internal_notes"),
        ),
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({"message": "Universite ajoutee avec succes.", "id": new_id}), 201


@app.route("/api/universities/<int:university_id>", methods=["GET"])
@require_role("admin", "conseiller")
def get_university(university_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_universities_table(cursor)
    cursor.execute("SELECT * FROM universities WHERE id = %s", (university_id,))
    university = cursor.fetchone()
    cursor.close()
    conn.close()

    if not university:
        return jsonify({"message": "Universite introuvable."}), 404

    return jsonify(rows_to_json([university])[0])


@app.route("/api/universities/<int:university_id>", methods=["DELETE"])
@require_role("admin")
def delete_university(university_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_universities_table(cursor)
    cursor.execute("DELETE FROM universities WHERE id = %s", (university_id,))
    conn.commit()
    deleted = cursor.rowcount
    cursor.close()
    conn.close()

    if not deleted:
        return jsonify({"message": "Universite introuvable."}), 404

    return jsonify({"message": "Universite supprimee avec succes."}), 200


@app.route("/api/leads", methods=["GET"])
@require_role("admin", "conseiller")
def get_leads():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_leads_table(cursor)
    columns = get_table_columns(cursor, "leads")
    order_column = "created_at" if "created_at" in columns else "id"
    cursor.execute(f"SELECT * FROM leads ORDER BY {order_column} DESC")
    leads = [normalize_lead_row(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return jsonify(leads)


@app.route("/api/leads", methods=["POST"])
@require_role("admin", "conseiller")
def add_lead():
    data = get_request_data()

    if not data.get("full_name"):
        return jsonify({"message": "Le nom complet est requis."}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_leads_table(cursor)
    ensure_status_history_table(cursor)
    columns = get_table_columns(cursor, "leads")

    incoming_values = {
        "full_name": data.get("full_name"),
        "name": data.get("full_name"),
        "phone": data.get("phone"),
        "whatsapp": data.get("whatsapp"),
        "email": data.get("email"),
        "study_level": data.get("study_level"),
        "average_score": data.get("average_score"),
        "budget": data.get("budget") or None,
        "desired_destination": data.get("desired_destination"),
        "speciality": data.get("speciality"),
        "source": data.get("source") or "Saisie CRM",
        "assigned_conseiller_id": data.get("assigned_conseiller_id") or None,
        "influencer_id": data.get("influencer_id") or None,
        "agent_id": data.get("agent_id") or None,
        "status": "Nouveau lead",
        "estimated_revenue": data.get("estimated_revenue") or 0,
        "internal_notes": data.get("internal_notes"),
    }
    insert_columns = [column for column in incoming_values if column in columns]
    placeholders = ", ".join(["%s"] * len(insert_columns))
    column_sql = ", ".join(insert_columns)
    values = [incoming_values[column] for column in insert_columns]

    cursor.execute(f"INSERT INTO leads ({column_sql}) VALUES ({placeholders})", values)
    lead_id = cursor.lastrowid
    if table_exists(cursor, "lead_status_history"):
        cursor.execute(
            """
            INSERT INTO lead_status_history (lead_id, old_status, new_status, changed_by_user_id, note)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (lead_id, None, "Nouveau lead", data.get("changed_by_user_id") or None, "Lead cree."),
        )
    lead_name = data.get("full_name", "Nouveau lead")
    notify_admins(cursor, "Nouveau lead cree", f"{lead_name} a ete ajoute dans le pipeline.", f"/leads/{lead_id}")
    influencer_id = data.get("influencer_id")
    if influencer_id:
        notify_user(cursor, "influencer", int(influencer_id), "Nouveau lead avec votre code",
                    f"{lead_name} s'est inscrit en utilisant votre code promo.", f"/influencer/leads")
    cursor.execute("SELECT email FROM users WHERE role = 'admin' AND is_active = TRUE")
    admin_emails = [r["email"] for r in cursor.fetchall() if r.get("email")]
    conseiller_id = data.get("assigned_conseiller_id")
    conseiller_email = None
    if conseiller_id:
        cursor.execute("SELECT email FROM users WHERE id = %s", (conseiller_id,))
        row = cursor.fetchone()
        if row and row.get("email"):
            conseiller_email = row["email"]
    recipient_emails = list(admin_emails)
    if conseiller_email and conseiller_email not in recipient_emails:
        recipient_emails.append(conseiller_email)
    ctx = {
        "full_name": lead_name,
        "phone": data.get("phone") or "-",
        "email": data.get("email") or "-",
        "destination": data.get("desired_destination") or "-",
        "speciality": data.get("speciality") or "-",
        "source": data.get("source") or "-",
        "revenue": str(data.get("estimated_revenue") or 0),
        "link": "http://127.0.0.1:5500/frontend/dashboard.html",
    }
    if recipient_emails:
        send_email(recipient_emails, "We Learn - Nouveau lead", EMAIL_TEMPLATES["nouveau_lead"].format(**ctx))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Lead enregistre avec succes.", "id": lead_id}), 201


@app.route("/api/leads/<int:lead_id>", methods=["PUT"])
@require_role("admin", "conseiller")
def update_lead(lead_id):
    data = get_request_data()
    full_name = (data.get("full_name") or "").strip()
    if not full_name:
        return jsonify({"message": "Le nom complet est requis."}), 400
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_leads_table(cursor)
    cursor.execute("SELECT id FROM leads WHERE id = %s", (lead_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"message": "Lead introuvable."}), 404
    columns = get_table_columns(cursor, "leads")
    values_by_column = {
        "full_name": full_name, "name": full_name, "phone": data.get("phone"),
        "whatsapp": data.get("whatsapp"), "email": data.get("email"),
        "study_level": data.get("study_level"), "average_score": data.get("average_score"),
        "budget": data.get("budget") or None, "desired_destination": data.get("desired_destination"),
        "speciality": data.get("speciality"), "source": data.get("source"),
        "estimated_revenue": data.get("estimated_revenue") or 0, "internal_notes": data.get("internal_notes"),
    }
    updates = [f"{column} = %s" for column in values_by_column if column in columns]
    values = [values_by_column[column] for column in values_by_column if column in columns]
    values.append(lead_id)
    cursor.execute(f"UPDATE leads SET {', '.join(updates)} WHERE id = %s", values)
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Lead mis a jour avec succes."})


@app.route("/api/leads/<int:lead_id>", methods=["DELETE"])
@require_role("admin", "conseiller")
def delete_lead(lead_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_lead_documents_table(cursor)
    cursor.execute("SELECT file_path FROM lead_documents WHERE lead_id = %s", (lead_id,))
    documents = cursor.fetchall()
    cursor.execute("DELETE FROM lead_documents WHERE lead_id = %s", (lead_id,))
    if table_exists(cursor, "lead_status_history"):
        cursor.execute("DELETE FROM lead_status_history WHERE lead_id = %s", (lead_id,))
    cursor.execute("DELETE FROM leads WHERE id = %s", (lead_id,))
    deleted = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    if not deleted:
        return jsonify({"message": "Lead introuvable."}), 404
    for document in documents:
        file_path = os.path.join(UPLOAD_FOLDER, document["file_path"])
        if os.path.exists(file_path):
            os.remove(file_path)
    return jsonify({"message": "Lead supprime avec succes."})


@app.route("/api/account-link", methods=["GET"])
@require_role("admin", "conseiller", "influencer", "agent")
def get_account_link():
    role = request.headers.get("X-User-Role")
    account_id = request.headers.get("X-User-Id")
    table_name = {"admin": "users", "conseiller": "users", "influencer": "influencers", "agent": "agents"}[role]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if table_name == "agents":
        ensure_agents_table(cursor)
    elif table_name == "influencers":
        ensure_influencers_table(cursor)
    else:
        ensure_users_table(cursor)
    ensure_public_token_column(cursor, table_name)
    cursor.execute(f"SELECT public_token FROM {table_name} WHERE id = %s AND is_active = TRUE", (account_id,))
    account = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    if not account:
        return jsonify({"message": "Compte introuvable ou inactif."}), 404
    return jsonify({"token": account["public_token"]})


@app.route("/api/public/leads", methods=["POST"])
def add_public_lead():
    data = get_request_data()
    token = (data.get("token") or "").strip()
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    phone = (data.get("phone") or "").strip()
    email = (data.get("email") or "").strip()
    if not token or not first_name or not last_name or not phone or not email:
        return jsonify({"message": "Nom, prenom, telephone et email sont requis."}), 400
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    account = None
    for account_type, table_name in (("user", "users"), ("influencer", "influencers"), ("agent", "agents")):
        if table_name == "users":
            ensure_users_table(cursor)
        elif table_name == "influencers":
            ensure_influencers_table(cursor)
        else:
            ensure_agents_table(cursor)
        ensure_public_token_column(cursor, table_name)
        cursor.execute(f"SELECT id FROM {table_name} WHERE public_token = %s AND is_active = TRUE", (token,))
        row = cursor.fetchone()
        if row:
            account = {"type": account_type, "id": row["id"]}
            break
    if not account:
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Ce lien de formulaire est invalide ou desactive."}), 404
    ensure_leads_table(cursor)
    ensure_status_history_table(cursor)
    columns = get_table_columns(cursor, "leads")
    full_name = f"{first_name} {last_name}"
    values_by_column = {
        "full_name": full_name, "name": full_name, "phone": phone, "whatsapp": data.get("whatsapp") or phone,
        "email": email, "study_level": data.get("study_level"), "speciality": data.get("speciality"),
        "desired_destination": data.get("desired_destination"), "source": "Formulaire public",
        "internal_notes": data.get("study_information"), "status": "Nouveau lead",
        "assigned_conseiller_id": account["id"] if account["type"] == "user" else None,
        "influencer_id": account["id"] if account["type"] == "influencer" else None,
        "agent_id": account["id"] if account["type"] == "agent" else None,
    }
    insert_columns = [column for column in values_by_column if column in columns]
    cursor.execute(f"INSERT INTO leads ({', '.join(insert_columns)}) VALUES ({', '.join(['%s'] * len(insert_columns))})",
                   [values_by_column[column] for column in insert_columns])
    lead_id = cursor.lastrowid
    cursor.execute("INSERT INTO lead_status_history (lead_id, old_status, new_status, note) VALUES (%s, %s, %s, %s)",
                   (lead_id, None, "Nouveau lead", "Lead cree depuis un formulaire public."))
    notify_admins(cursor, "Nouveau lead cree", f"{full_name} a ete ajoute dans le pipeline.", f"/leads/{lead_id}")
    target_type = "conseiller" if account["type"] == "user" else account["type"]
    notify_user(cursor, target_type, account["id"], "Nouveau lead", f"{full_name} a utilise votre lien de formulaire.", f"/leads/{lead_id}")
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Votre demande a ete envoyee avec succes."}), 201


@app.route("/api/leads/<int:lead_id>/status", methods=["PUT"])
@require_role("admin", "conseiller")
def update_lead_status(lead_id):
    data = get_request_data()
    new_status = data.get("status")

    if new_status not in PIPELINE_STATUSES:
        return jsonify({"message": "Statut invalide."}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM leads WHERE id = %s", (lead_id,))
    lead = cursor.fetchone()

    if not lead:
        cursor.close()
        conn.close()
        return jsonify({"message": "Lead introuvable."}), 404

    old_status = lead["status"]
    lead_name = lead.get("full_name") or lead.get("name") or "Lead"
    cursor.execute("UPDATE leads SET status = %s WHERE id = %s", (new_status, lead_id))
    cursor.execute(
        """
        INSERT INTO lead_status_history (lead_id, old_status, new_status, changed_by_user_id, note)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            lead_id,
            old_status,
            new_status,
            data.get("changed_by_user_id") or None,
            data.get("note"),
        ),
    )
    notify_admins(cursor, "Statut de lead modifie",
                  f"Le statut de {lead_name} est passe de '{old_status}' a '{new_status}'.",
                  f"/leads/{lead_id}")
    if lead["assigned_conseiller_id"]:
        notify_user(cursor, "conseiller", lead["assigned_conseiller_id"], "Mise a jour de dossier",
                    f"Le statut de {lead_name} a ete mis a jour.", f"/leads/{lead_id}")
    if lead["influencer_id"]:
        notify_user(cursor, "influencer", lead["influencer_id"], "Evolution de votre lead",
                    f"Le dossier de {lead_name} est maintenant: {new_status}.", "/influencer/leads")
    send_email_flag = data.get("send_email")
    if send_email_flag is None:
        send_email_flag = new_status in ("Admission obtenue", "Paiement effectue", "Visa obtenu", "Depart confirme")
    if send_email_flag and new_status in ("Admission obtenue", "Paiement effectue", "Visa obtenu", "Depart confirme"):
        cursor.execute("SELECT email FROM users WHERE role = 'admin' AND is_active = TRUE")
        admin_emails = [r["email"] for r in cursor.fetchall() if r.get("email")]
        conseiller_email = None
        if lead["assigned_conseiller_id"]:
            cursor.execute("SELECT email FROM users WHERE id = %s", (lead["assigned_conseiller_id"],))
            row = cursor.fetchone()
            if row and row.get("email"):
                conseiller_email = row["email"]
        recipient_emails = list(admin_emails)
        if conseiller_email and conseiller_email not in recipient_emails:
            recipient_emails.append(conseiller_email)
        if lead.get("email"):
            recipient_emails.append(lead["email"])
        key_map = {
            "Admission obtenue": "admission",
            "Paiement effectue": "paiement",
            "Visa obtenu": "visa",
            "Depart confirme": "depart",
        }
        ctx = {
            "full_name": lead_name,
            "link": "http://127.0.0.1:5500/frontend/dashboard.html",
        }
        if recipient_emails:
            send_email(recipient_emails, f"We Learn - {new_status}", EMAIL_TEMPLATES[key_map[new_status]].format(**ctx))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Statut mis a jour avec succes."}), 200


@app.route("/api/leads/<int:lead_id>/history", methods=["GET"])
@require_role("admin", "conseiller")
def get_lead_history(lead_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT lead_status_history.*, users.name AS changed_by_name
        FROM lead_status_history
        LEFT JOIN users ON users.id = lead_status_history.changed_by_user_id
        WHERE lead_status_history.lead_id = %s
        ORDER BY lead_status_history.changed_at DESC
        """,
        (lead_id,),
    )
    history = rows_to_json(cursor.fetchall())
    cursor.close()
    conn.close()
    return jsonify(history)


@app.route("/api/dashboard/kpis", methods=["GET"])
@require_role("admin", "conseiller")
def get_dashboard_kpis():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_leads_table(cursor)
    columns = get_table_columns(cursor, "leads")
    revenue_sql = "COALESCE(SUM(estimated_revenue), 0)" if "estimated_revenue" in columns else "0"
    status_sql = "status" if "status" in columns else "'Nouveau lead'"
    cursor.execute(
        f"""
        SELECT
            COUNT(*) AS total_leads,
            SUM({status_sql} = 'Admission obtenue') AS admissions_obtenues,
            SUM({status_sql} = 'Visa obtenu') AS visas_obtenus,
            SUM({status_sql} = 'Depart confirme') AS departs_confirmes,
            {revenue_sql} AS chiffre_affaires_estime
        FROM leads
        """
    )
    kpis = cursor.fetchone() or {}
    total = kpis["total_leads"] or 0
    converted = kpis["departs_confirmes"] or 0
    kpis["taux_conversion"] = round((converted / total) * 100, 2) if total else 0
    cursor.close()
    conn.close()
    return jsonify({key: json_ready(value) for key, value in kpis.items()})


@app.route("/api/pipeline-statuses", methods=["GET"])
def get_pipeline_statuses():
    return jsonify(PIPELINE_STATUSES)


@app.route("/api/leads/<int:lead_id>/documents", methods=["GET"])
@require_role("admin", "conseiller")
def get_lead_documents(lead_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_lead_documents_table(cursor)
    cursor.execute(
        "SELECT * FROM lead_documents WHERE lead_id = %s ORDER BY uploaded_at DESC",
        (lead_id,),
    )
    docs = rows_to_json(cursor.fetchall())
    cursor.close()
    conn.close()
    return jsonify(docs)


@app.route("/api/leads/<int:lead_id>/documents", methods=["POST"])
@require_role("admin", "conseiller")
def upload_document(lead_id):
    if "file" not in request.files:
        return jsonify({"message": "Aucun fichier fourni."}), 400

    file = request.files["file"]
    if not file.filename or not allowed_file(file.filename):
        return jsonify({"message": "Type de fichier non autorise. Formats: PDF, PNG, JPG, DOC, DOCX, XLS, XLSX, ZIP."}), 400

    document_type = request.form.get("document_type", "Autre")
    if document_type not in DOCUMENT_TYPES:
        return jsonify({"message": "Type de document invalide."}), 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_name)
    file.save(file_path)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_lead_documents_table(cursor)
    user_id = request.form.get("uploaded_by_user_id") or None
    cursor.execute(
        """
        INSERT INTO lead_documents (lead_id, document_type, file_name, file_path, uploaded_by_user_id)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (lead_id, document_type, file.filename, unique_name, user_id),
    )
    conn.commit()
    doc_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({"message": "Document uploade avec succes.", "id": doc_id}), 201


@app.route("/api/documents/<int:doc_id>", methods=["DELETE"])
@require_role("admin", "conseiller")
def delete_document(doc_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT file_path FROM lead_documents WHERE id = %s", (doc_id,))
    doc = cursor.fetchone()

    if not doc:
        cursor.close()
        conn.close()
        return jsonify({"message": "Document introuvable."}), 404

    file_to_delete = os.path.join(UPLOAD_FOLDER, doc["file_path"])
    if os.path.exists(file_to_delete):
        os.remove(file_to_delete)

    cursor.execute("DELETE FROM lead_documents WHERE id = %s", (doc_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Document supprime avec succes."}), 200


@app.route("/api/documents/<int:doc_id>/download", methods=["GET"])
def download_document(doc_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT file_name, file_path FROM lead_documents WHERE id = %s", (doc_id,))
    doc = cursor.fetchone()
    cursor.close()
    conn.close()

    if not doc:
        return jsonify({"message": "Document introuvable."}), 404

    return send_from_directory(UPLOAD_FOLDER, doc["file_path"], download_name=doc["file_name"], as_attachment=True)


@app.route("/api/document-types", methods=["GET"])
def get_document_types():
    return jsonify(DOCUMENT_TYPES)


@app.route("/api/admin/users", methods=["GET"])
@require_role("admin")
def admin_get_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_users_table(cursor)
    cursor.execute("SELECT id, name, email, role, is_active, created_at FROM users ORDER BY created_at DESC")
    users = rows_to_json(cursor.fetchall())
    cursor.close()
    conn.close()
    return jsonify(users)


@app.route("/api/admin/users", methods=["POST"])
@require_role("admin")
def admin_add_user():
    data = get_request_data()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    role = data.get("role", "conseiller")

    if not name or not email or not password:
        return jsonify({"message": "Nom, email et mot de passe sont requis."}), 400
    if role not in ("admin", "conseiller"):
        return jsonify({"message": "Role invalide."}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_users_table(cursor)
    try:
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, password, role),
        )
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({"message": "Utilisateur ajoute avec succes.", "id": new_id}), 201
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        if "Duplicate" in str(e):
            return jsonify({"message": "Cet email est deja utilise."}), 409
        return jsonify({"message": "Erreur lors de l'ajout."}), 500


@app.route("/api/admin/users/<int:user_id>", methods=["PUT"])
@require_role("admin")
def admin_update_user(user_id):
    data = get_request_data()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"message": "Utilisateur introuvable."}), 404

    updates = []
    values = []
    for field in ["name", "email", "role"]:
        if field in data:
            updates.append(f"{field} = %s")
            values.append(data[field])
    if "password" in data and data["password"]:
        updates.append("password = %s")
        values.append(data["password"])

    if not updates:
        cursor.close()
        conn.close()
        return jsonify({"message": "Aucune donnee a mettre a jour."}), 400

    values.append(user_id)
    try:
        cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = %s", values)
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Utilisateur mis a jour avec succes."}), 200
    except Exception:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"message": "Erreur lors de la mise a jour."}), 500


@app.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
@require_role("admin")
def admin_delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    deleted = cursor.rowcount
    cursor.close()
    conn.close()
    if not deleted:
        return jsonify({"message": "Utilisateur introuvable."}), 404
    return jsonify({"message": "Utilisateur supprime avec succes."}), 200


@app.route("/api/influencer/<int:influencer_id>/dashboard", methods=["GET"])
def influencer_dashboard(influencer_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_commissions_table(cursor)

    cursor.execute("SELECT id, name, email, promo_code, commission_rate FROM influencers WHERE id = %s", (influencer_id,))
    profile = cursor.fetchone()
    if not profile:
        cursor.close()
        conn.close()
        return jsonify({"message": "Influenceur introuvable."}), 404

    cursor.execute("SELECT COUNT(*) AS total FROM leads WHERE influencer_id = %s", (influencer_id,))
    total_leads = cursor.fetchone()["total"]

    cursor.execute(
        """
        SELECT
            COALESCE(SUM(CASE WHEN status = 'estimee' THEN amount ELSE 0 END), 0) AS estime,
            COALESCE(SUM(CASE WHEN status = 'validee' THEN amount ELSE 0 END), 0) AS valide,
            COALESCE(SUM(CASE WHEN status = 'payee' THEN amount ELSE 0 END), 0) AS paye
        FROM commissions WHERE influencer_id = %s
        """,
        (influencer_id,),
    )
    comm = cursor.fetchone()

    cursor.execute(
        "SELECT COUNT(*) AS cnt FROM commissions WHERE influencer_id = %s AND status = 'payee'",
        (influencer_id,),
    )
    commissions_payees = cursor.fetchone()["cnt"]

    cursor.close()
    conn.close()
    return jsonify({
        "profile": profile,
        "total_leads": total_leads,
        "commissions_estimees": float(comm["estime"]),
        "commissions_validees": float(comm["valide"]),
        "commissions_payees": float(comm["paye"]),
        "total_commissions_payees_count": commissions_payees,
    })


@app.route("/api/influencer/<int:influencer_id>/leads", methods=["GET"])
def influencer_leads(influencer_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT id, name AS full_name, phone, email, desired_destination, speciality, status, created_at
        FROM leads WHERE influencer_id = %s ORDER BY created_at DESC
        """,
        (influencer_id,),
    )
    leads = rows_to_json(cursor.fetchall())
    cursor.close()
    conn.close()
    return jsonify(leads)


@app.route("/api/influencer/<int:influencer_id>/commissions", methods=["GET"])
def influencer_commissions(influencer_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_commissions_table(cursor)
    cursor.execute(
        """
        SELECT c.*, l.name AS lead_name
        FROM commissions c
        LEFT JOIN leads l ON l.id = c.lead_id
        WHERE c.influencer_id = %s
        ORDER BY c.created_at DESC
        """,
        (influencer_id,),
    )
    commissions = rows_to_json(cursor.fetchall())
    cursor.close()
    conn.close()
    return jsonify(commissions)


def ensure_influencers_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS influencers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(120) NOT NULL,
            email VARCHAR(160) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            promo_code VARCHAR(80) NOT NULL UNIQUE,
            commission_rate DECIMAL(5,2) NOT NULL DEFAULT 0.00,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )


@app.route("/api/admin/influencers", methods=["GET"])
@require_role("admin")
def admin_get_influencers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_influencers_table(cursor)
    cursor.execute("SELECT id, name, email, promo_code, commission_rate, is_active, created_at FROM influencers ORDER BY created_at DESC")
    influencers = rows_to_json(cursor.fetchall())
    cursor.close()
    conn.close()
    return jsonify(influencers)


@app.route("/api/admin/influencers", methods=["POST"])
@require_role("admin")
def admin_add_influencer():
    data = get_request_data()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    promo_code = data.get("promo_code", "").strip()
    commission_rate = data.get("commission_rate", 0)

    if not name or not email or not password or not promo_code:
        return jsonify({"message": "Nom, email, mot de passe et code promo sont requis."}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_influencers_table(cursor)
    try:
        cursor.execute(
            "INSERT INTO influencers (name, email, password, promo_code, commission_rate) VALUES (%s, %s, %s, %s, %s)",
            (name, email, password, promo_code, commission_rate),
        )
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({"message": "Influenceur ajoute avec succes.", "id": new_id}), 201
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        error_msg = str(e)
        if "Duplicate" in error_msg:
            if "email" in error_msg:
                return jsonify({"message": "Cet email est deja utilise."}), 409
            return jsonify({"message": "Ce code promo est deja utilise."}), 409
        return jsonify({"message": "Erreur lors de l'ajout."}), 500


@app.route("/api/admin/influencers/<int:influencer_id>", methods=["PUT"])
@require_role("admin")
def admin_update_influencer(influencer_id):
    data = get_request_data()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id FROM influencers WHERE id = %s", (influencer_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"message": "Influenceur introuvable."}), 404

    updates = []
    values = []
    for field in ["name", "email", "promo_code", "commission_rate"]:
        if field in data:
            updates.append(f"{field} = %s")
            values.append(data[field])
    if "password" in data and data["password"]:
        updates.append("password = %s")
        values.append(data["password"])

    if not updates:
        cursor.close()
        conn.close()
        return jsonify({"message": "Aucune donnee a mettre a jour."}), 400

    values.append(influencer_id)
    try:
        cursor.execute(f"UPDATE influencers SET {', '.join(updates)} WHERE id = %s", values)
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Influenceur mis a jour avec succes."}), 200
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"message": "Erreur lors de la mise a jour."}), 500


@app.route("/api/admin/influencers/<int:influencer_id>", methods=["DELETE"])
@require_role("admin")
def admin_delete_influencer(influencer_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("DELETE FROM influencers WHERE id = %s", (influencer_id,))
    conn.commit()
    deleted = cursor.rowcount
    cursor.close()
    conn.close()

    if not deleted:
        return jsonify({"message": "Influenceur introuvable."}), 404
    return jsonify({"message": "Influenceur supprime avec succes."}), 200


@app.route("/api/notifications", methods=["GET"])
@require_role("admin", "conseiller", "influencer")
def get_notifications():
    role = request.headers.get("X-User-Role")
    user_id = int(request.headers.get("X-User-Id"))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_notifications_table(cursor)

    if role == "influencer":
        cursor.execute(
            "SELECT * FROM notifications WHERE target_type = 'influencer' AND target_id = %s ORDER BY created_at DESC LIMIT 50",
            (user_id,),
        )
    else:
        cursor.execute(
            """
            SELECT * FROM notifications
            WHERE (target_type = %s AND (target_id IS NULL OR target_id = %s))
               OR (target_type = 'admin' AND target_id IN (SELECT id FROM users WHERE role = 'admin' AND is_active = TRUE))
            ORDER BY created_at DESC LIMIT 50
            """,
            (role, user_id),
        )
    notifs = rows_to_json(cursor.fetchall())
    cursor.close()
    conn.close()
    return jsonify(notifs)


@app.route("/api/notifications/unread-count", methods=["GET"])
@require_role("admin", "conseiller", "influencer")
def get_unread_notification_count():
    role = request.headers.get("X-User-Role")
    user_id = int(request.headers.get("X-User-Id"))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_notifications_table(cursor)

    if role == "influencer":
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM notifications WHERE target_type = 'influencer' AND target_id = %s AND is_read = FALSE",
            (user_id,),
        )
    else:
        cursor.execute(
            """
            SELECT COUNT(*) AS cnt FROM notifications
            WHERE (target_type = %s AND (target_id IS NULL OR target_id = %s) AND is_read = FALSE)
               OR (target_type = 'admin' AND target_id IN (SELECT id FROM users WHERE role = 'admin' AND is_active = TRUE) AND is_read = FALSE)
            """,
            (role, user_id),
        )
    cnt = cursor.fetchone()["cnt"]
    cursor.close()
    conn.close()
    return jsonify({"count": cnt})


@app.route("/api/notifications/<int:notif_id>/read", methods=["PUT"])
@require_role("admin", "conseiller", "influencer")
def mark_notification_read(notif_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("UPDATE notifications SET is_read = TRUE WHERE id = %s", (notif_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Notification marquee comme lue."}), 200


@app.route("/api/notifications/read-all", methods=["PUT"])
@require_role("admin", "conseiller", "influencer")
def mark_all_notifications_read():
    role = request.headers.get("X-User-Role")
    user_id = int(request.headers.get("X-User-Id"))
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_notifications_table(cursor)

    if role == "influencer":
        cursor.execute(
            "UPDATE notifications SET is_read = TRUE WHERE target_type = 'influencer' AND target_id = %s",
            (user_id,),
        )
    else:
        cursor.execute(
            """
            UPDATE notifications SET is_read = TRUE
            WHERE (target_type = %s AND (target_id IS NULL OR target_id = %s))
               OR (target_type = 'admin' AND target_id IN (SELECT id FROM users WHERE role = 'admin' AND is_active = TRUE))
            """,
            (role, user_id),
        )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Toutes les notifications ont ete marquees comme lues."}), 200


@app.route("/api/profile", methods=["PUT"])
@require_role("admin", "conseiller")
def update_own_profile():
    data = get_request_data()
    user_id = request.headers.get("X-User-Id")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    updates = []
    values = []
    if "name" in data and data["name"]:
        updates.append("name = %s")
        values.append(data["name"])
    if "password" in data and data["password"]:
        updates.append("password = %s")
        values.append(data["password"])

    if not updates:
        cursor.close()
        conn.close()
        return jsonify({"message": "Aucune donnee a mettre a jour."}), 400

    values.append(user_id)
    try:
        cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = %s", values)
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Profil mis a jour avec succes."}), 200
    except Exception:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"message": "Erreur lors de la mise a jour."}), 500


@app.route("/api/profile", methods=["GET"])
@require_role("admin", "conseiller")
def get_own_profile():
    user_id = request.headers.get("X-User-Id")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_public_token_column(cursor, "users")
    cursor.execute("SELECT id, name, email, role FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if not user:
        return jsonify({"message": "Utilisateur introuvable."}), 404
    return jsonify(user)


def ensure_agents_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS agents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(120) NOT NULL,
            email VARCHAR(160) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            country VARCHAR(120) DEFAULT '',
            address TEXT,
            logo VARCHAR(500) DEFAULT '',
            facebook VARCHAR(255) DEFAULT '',
            website VARCHAR(255) DEFAULT '',
            instagram VARCHAR(255) DEFAULT '',
            snapchat VARCHAR(255) DEFAULT '',
            public_token VARCHAR(64) NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )


def ensure_agent_documents_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_documents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            agent_id INT NOT NULL,
            document_type VARCHAR(80) NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )


def seed_agent_if_empty(cursor):
    ensure_agents_table(cursor)
    cursor.execute("SELECT COUNT(*) AS total FROM agents")
    total = cursor.fetchone()["total"]
    if total:
        return
    cursor.execute(
        "INSERT INTO agents (name, email, password, country, facebook, website, instagram) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        ("WE LEARN", "agent@welearn.com", "agent123", "Tunisia", "We learn consulting", "www.welearntunisia.com", "welearn_consulting"),
    )


@app.route("/api/agent/login", methods=["POST"])
def agent_login():
    data = get_request_data()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"status": "error", "message": "Email et mot de passe requis."}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_agents_table(cursor)
    seed_agent_if_empty(cursor)
    conn.commit()

    cursor.execute(
        "SELECT id, name, email, password FROM agents WHERE email = %s AND is_active = TRUE",
        (email,),
    )
    agent = cursor.fetchone()
    cursor.close()
    conn.close()

    if agent and agent["password"] == password:
        agent.pop("password", None)
        return jsonify({"status": "success", "user": agent, "type": "agent"}), 200

    return jsonify({"status": "error", "message": "Email ou mot de passe incorrect."}), 401


@app.route("/api/agent/<int:agent_id>/profile", methods=["GET"])
@require_role("agent")
def get_agent_profile(agent_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_agents_table(cursor)
    cursor.execute(
        "SELECT id, name, email, country, address, logo, facebook, website, instagram, snapchat FROM agents WHERE id = %s",
        (agent_id,),
    )
    agent = cursor.fetchone()
    cursor.close()
    conn.close()

    if not agent:
        return jsonify({"message": "Agent introuvable."}), 404

    return jsonify(agent)


@app.route("/api/agent/<int:agent_id>/profile", methods=["PUT"])
@require_role("agent")
def update_agent_profile(agent_id):
    data = get_request_data()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_agents_table(cursor)

    cursor.execute("SELECT id FROM agents WHERE id = %s", (agent_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"message": "Agent introuvable."}), 404

    updates = []
    values = []
    for field in ["name", "country", "address", "facebook", "website", "instagram", "snapchat"]:
        if field in data:
            updates.append(f"{field} = %s")
            values.append(data[field])
    if "password" in data and data["password"]:
        updates.append("password = %s")
        values.append(data["password"])
    if "logo" in data:
        updates.append("logo = %s")
        values.append(data["logo"])

    if not updates:
        cursor.close()
        conn.close()
        return jsonify({"message": "Aucune donnee a mettre a jour."}), 400

    values.append(agent_id)
    try:
        cursor.execute(f"UPDATE agents SET {', '.join(updates)} WHERE id = %s", values)
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Profil mis a jour avec succes."}), 200
    except Exception:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"message": "Erreur lors de la mise a jour."}), 500


@app.route("/api/agent/<int:agent_id>/documents", methods=["GET"])
@require_role("agent")
def get_agent_documents(agent_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_agent_documents_table(cursor)
    cursor.execute(
        "SELECT * FROM agent_documents WHERE agent_id = %s ORDER BY uploaded_at DESC",
        (agent_id,),
    )
    docs = rows_to_json(cursor.fetchall())
    cursor.close()
    conn.close()
    return jsonify(docs)


@app.route("/api/agent/<int:agent_id>/documents", methods=["POST"])
@require_role("agent")
def upload_agent_document(agent_id):
    if "file" not in request.files:
        return jsonify({"message": "Aucun fichier fourni."}), 400

    file = request.files["file"]
    if not file.filename or not allowed_file(file.filename):
        return jsonify({"message": "Type de fichier non autorise."}), 400

    document_type = request.form.get("document_type", "Autre")
    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_name)
    file.save(file_path)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_agent_documents_table(cursor)
    cursor.execute(
        "INSERT INTO agent_documents (agent_id, document_type, file_name, file_path) VALUES (%s, %s, %s, %s)",
        (agent_id, document_type, file.filename, unique_name),
    )
    conn.commit()
    doc_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({"message": "Document uploade avec succes.", "id": doc_id}), 201


@app.route("/api/agent/documents/<int:doc_id>", methods=["DELETE"])
@require_role("agent")
def delete_agent_document(doc_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT file_path FROM agent_documents WHERE id = %s", (doc_id,))
    doc = cursor.fetchone()

    if not doc:
        cursor.close()
        conn.close()
        return jsonify({"message": "Document introuvable."}), 404

    file_to_delete = os.path.join(UPLOAD_FOLDER, doc["file_path"])
    if os.path.exists(file_to_delete):
        os.remove(file_to_delete)

    cursor.execute("DELETE FROM agent_documents WHERE id = %s", (doc_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Document supprime avec succes."}), 200


@app.route("/api/agent/documents/<int:doc_id>/download", methods=["GET"])
def download_agent_document(doc_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT file_name, file_path FROM agent_documents WHERE id = %s", (doc_id,))
    doc = cursor.fetchone()
    cursor.close()
    conn.close()

    if not doc:
        return jsonify({"message": "Document introuvable."}), 404

    return send_from_directory(UPLOAD_FOLDER, doc["file_path"], download_name=doc["file_name"], as_attachment=True)


@app.route("/api/applications", methods=["GET"])
def get_applications():
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return jsonify({"message": "Authentification requise."}), 401
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    status_filter = request.args.get("status")
    search = request.args.get("search", "").strip()
    query = """
        SELECT a.*, u.name AS creator_name
        FROM applications a
        LEFT JOIN users u ON a.created_by = u.id
    """
    params = []
    wheres = []
    if status_filter:
        wheres.append("a.status = %s")
        params.append(status_filter)
    if search:
        wheres.append("(a.student_name LIKE %s OR a.program_name LIKE %s OR a.university_name LIKE %s)")
        like = f"%{search}%"
        params.extend([like, like, like])
    if wheres:
        query += " WHERE " + " AND ".join(wheres)
    query += " ORDER BY a.created_at DESC"
    cursor.execute(query, params)
    rows = rows_to_json(cursor.fetchall())
    cursor.close()
    conn.close()
    for r in rows:
        for k, v in r.items():
            if isinstance(v, (date, datetime)):
                r[k] = v.isoformat()
    return jsonify(rows)


@app.route("/api/applications/status-counts", methods=["GET"])
def application_status_counts():
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return jsonify({"message": "Authentification requise."}), 401
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT status, COUNT(*) AS cnt FROM applications GROUP BY status")
    counts = {row["status"]: row["cnt"] for row in cursor.fetchall()}
    cursor.execute("SELECT COUNT(*) AS total FROM applications")
    counts["total"] = cursor.fetchone()["total"]
    cursor.close()
    conn.close()
    return jsonify(counts)


@app.route("/api/applications", methods=["POST"])
def add_application():
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return jsonify({"message": "Authentification requise."}), 401
    data = get_request_data()
    student_name = (data.get("student_name") or "").strip()
    if not student_name:
        return jsonify({"message": "Le nom de l'etudiant est requis."}), 400
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """INSERT INTO applications
           (student_name, phone, whatsapp, email, university_name, program_name,
            academic_year, status, created_by, internal_notes)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            student_name,
            data.get("phone", ""),
            data.get("whatsapp", ""),
            data.get("email", ""),
            data.get("university_name", ""),
            data.get("program_name", ""),
            data.get("academic_year", ""),
            data.get("status", "pending_review"),
            user_id,
            data.get("internal_notes", ""),
        ),
    )
    conn.commit()
    app_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({"message": "Candidature creee.", "id": app_id}), 201


@app.route("/api/applications/<int:app_id>", methods=["GET"])
def get_application(app_id):
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return jsonify({"message": "Authentification requise."}), 401
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT a.*, u.name AS creator_name FROM applications a LEFT JOIN users u ON a.created_by = u.id WHERE a.id = %s",
        (app_id,),
    )
    app = cursor.fetchone()
    cursor.close()
    conn.close()
    if not app:
        return jsonify({"message": "Candidature introuvable."}), 404
    for k, v in app.items():
        if isinstance(v, (date, datetime)):
            app[k] = v.isoformat()
    return jsonify(app)


@app.route("/api/applications/<int:app_id>", methods=["PUT"])
def update_application(app_id):
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return jsonify({"message": "Authentification requise."}), 401
    data = get_request_data()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM applications WHERE id = %s", (app_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"message": "Candidature introuvable."}), 404
    fields = ["student_name", "phone", "whatsapp", "email", "university_name",
              "program_name", "academic_year", "status", "internal_notes"]
    sets = []
    params = []
    for f in fields:
        if f in data:
            sets.append(f"{f} = %s")
            params.append(data[f])
    if sets:
        params.append(app_id)
        cursor.execute(
            f"UPDATE applications SET {', '.join(sets)} WHERE id = %s", params
        )
        conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Candidature mise a jour."})


def ensure_appointments_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            lead_id INT NOT NULL,
            title VARCHAR(255) NOT NULL DEFAULT 'Rendez-vous',
            appointment_date DATE NOT NULL,
            appointment_time TIME NOT NULL,
            duration_minutes INT NOT NULL DEFAULT 60,
            location VARCHAR(255),
            type VARCHAR(20) NOT NULL DEFAULT 'présentiel',
            status VARCHAR(20) NOT NULL DEFAULT 'prévu',
            notes TEXT,
            created_by INT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    )


@app.route("/api/appointments", methods=["GET"])
@require_role("admin", "conseiller")
def get_appointments():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_appointments_table(cursor)
    conn.commit()
    filters = []
    params = []
    lead_id = request.args.get("lead_id")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    status = request.args.get("status")
    if lead_id:
        filters.append("a.lead_id = %s")
        params.append(lead_id)
    if date_from:
        filters.append("a.appointment_date >= %s")
        params.append(date_from)
    if date_to:
        filters.append("a.appointment_date <= %s")
        params.append(date_to)
    if status:
        filters.append("a.status = %s")
        params.append(status)
    where = ("WHERE " + " AND ".join(filters)) if filters else ""
    lead_cols = get_table_columns(cursor, "leads")
    name_expr = "l.full_name" if "full_name" in lead_cols else "l.name" if "name" in lead_cols else "''"
    phone_expr = "l.phone" if "phone" in lead_cols else "''"
    whatsapp_expr = "l.whatsapp" if "whatsapp" in lead_cols else "''"
    email_expr = "l.email" if "email" in lead_cols else "''"
    cursor.execute(
        f"""
        SELECT a.*, {name_expr} AS lead_name, {phone_expr} AS lead_phone, {whatsapp_expr} AS lead_whatsapp, {email_expr} AS lead_email, u.name AS creator_name
        FROM appointments a
        LEFT JOIN leads l ON l.id = a.lead_id
        LEFT JOIN users u ON u.id = a.created_by
        {where}
        ORDER BY a.appointment_date ASC, a.appointment_time ASC
        """,
        params,
    )
    rows = rows_to_json(cursor.fetchall())
    cursor.close()
    conn.close()
    return jsonify(rows)


@app.route("/api/appointments", methods=["POST"])
@require_role("admin", "conseiller")
def create_appointment():
    data = get_request_data()
    lead_id = data.get("lead_id")
    appointment_date = data.get("appointment_date")
    appointment_time = data.get("appointment_time")
    if not lead_id or not appointment_date or not appointment_time:
        return jsonify({"message": "Lead, date et heure sont requis."}), 400
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_appointments_table(cursor)
    lead_cols2 = get_table_columns(cursor, "leads")
    name_col = "full_name" if "full_name" in lead_cols2 else "name" if "name" in lead_cols2 else "full_name"
    cursor.execute(f"SELECT id, {name_col} FROM leads WHERE id = %s", (lead_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"message": "Lead introuvable."}), 404
    cursor.execute(
        """
        INSERT INTO appointments (lead_id, title, appointment_date, appointment_time, duration_minutes, location, type, status, notes, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            lead_id,
            data.get("title") or "Rendez-vous",
            appointment_date,
            appointment_time,
            int(data.get("duration_minutes") or 60),
            data.get("location") or "",
            data.get("type") or "présentiel",
            data.get("status") or "prévu",
            data.get("notes") or "",
            request.headers.get("X-User-Id"),
        ),
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({"message": "Rendez-vous cree.", "id": new_id}), 201


@app.route("/api/appointments/<int:appointment_id>", methods=["PUT"])
@require_role("admin", "conseiller")
def update_appointment(appointment_id):
    data = get_request_data()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_appointments_table(cursor)
    cursor.execute("SELECT id FROM appointments WHERE id = %s", (appointment_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"message": "Rendez-vous introuvable."}), 404
    fields = ["title", "appointment_date", "appointment_time", "duration_minutes", "location", "type", "status", "notes", "lead_id"]
    sets = []
    params = []
    for f in fields:
        if f in data:
            sets.append(f"{f} = %s")
            params.append(data[f])
    if not sets:
        cursor.close()
        conn.close()
        return jsonify({"message": "Aucune donnee a mettre a jour."}), 400
    params.append(appointment_id)
    cursor.execute(f"UPDATE appointments SET {', '.join(sets)} WHERE id = %s", params)
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Rendez-vous mis a jour."})


@app.route("/api/appointments/<int:appointment_id>", methods=["DELETE"])
@require_role("admin", "conseiller")
def delete_appointment(appointment_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_appointments_table(cursor)
    cursor.execute("DELETE FROM appointments WHERE id = %s", (appointment_id,))
    conn.commit()
    deleted = cursor.rowcount
    cursor.close()
    conn.close()
    if not deleted:
        return jsonify({"message": "Rendez-vous introuvable."}), 404
    return jsonify({"message": "Rendez-vous supprime."})


@app.route("/api/appointments/<int:appointment_id>/email", methods=["POST"])
@require_role("admin", "conseiller")
def email_appointment(appointment_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    ensure_appointments_table(cursor)
    lead_cols = get_table_columns(cursor, "leads")
    email_expr = "l.email" if "email" in lead_cols else "''"
    name_expr = "l.full_name" if "full_name" in lead_cols else "l.name" if "name" in lead_cols else "''"
    cursor.execute(
        f"""
        SELECT a.*, {name_expr} AS lead_name, {email_expr} AS lead_email, l.phone AS lead_phone
        FROM appointments a LEFT JOIN leads l ON l.id = a.lead_id WHERE a.id = %s
        """,
        (appointment_id,),
    )
    apt = cursor.fetchone()
    if not apt:
        cursor.close()
        conn.close()
        return jsonify({"message": "Rendez-vous introuvable."}), 404
    lead_email = (apt.get("lead_email") or "").strip()
    if not lead_email:
        cursor.close()
        conn.close()
        return jsonify({"message": "Email du lead manquant."}), 400
    date_str = apt["appointment_date"].isoformat() if hasattr(apt["appointment_date"], "isoformat") else str(apt["appointment_date"])
    time_val = apt["appointment_time"]
    if hasattr(time_val, "isoformat"):
        time_str = time_val.isoformat()[:5]
    elif isinstance(time_val, timedelta):
        total = int(time_val.total_seconds()); h, rem = divmod(total, 3600); m, s = divmod(rem, 60); time_str = f"{h:02d}:{m:02d}"
    else:
        time_str = str(time_val)[:5]
    html = f"""<!DOCTYPE html><html><body style="font-family:Inter,sans-serif">
    <div style="max-width:600px;margin:20px auto;border:1px solid #eee;border-radius:12px;overflow:hidden">
    <div style="background:linear-gradient(135deg,rgb(9,107,120),rgb(0,55,60));padding:24px;color:rgb(241,208,106);text-align:center"><h2>Invitation Rendez-vous - We Learn</h2></div>
    <div style="padding:24px;color:rgb(9,36,58)">
    <p>Bonjour <strong>{apt.get('lead_name') or ''}</strong>,</p>
    <p>Votre rendez-vous <strong>{apt.get('title') or 'We Learn'}</strong> est prevu le <strong>{date_str} a {time_str}</strong> ({apt.get('type')}).</p>
    <p><strong>Lieu:</strong> {apt.get('location') or '-'}<br><strong>Duree:</strong> {apt.get('duration_minutes')} min<br><strong>Statut:</strong> {apt.get('status')}</p>
    <p><strong>Notes:</strong><br>{(apt.get('notes') or '-').replace(chr(10), '<br>')}</p>
    <p style="margin-top:16px">Merci de confirmer votre presence.</p>
    <p style="color:#888;font-size:12px">We Learn Consulting</p>
    </div></div></body></html>"""
    sent = send_email([lead_email], f"We Learn - Rendez-vous {date_str} {time_str}", html)
    cursor.close()
    conn.close()
    if not sent:
        return jsonify({"message": "Email non configure ou echec d'envoi (verifiez MAIL_USERNAME/PASSWORD)."}), 500
    return jsonify({"message": "Email envoye a " + lead_email})


@app.route("/api/applications/<int:app_id>", methods=["DELETE"])
def delete_application(app_id):
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return jsonify({"message": "Authentification requise."}), 401
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("DELETE FROM applications WHERE id = %s", (app_id,))
    conn.commit()
    deleted = cursor.rowcount
    cursor.close()
    conn.close()
    if not deleted:
        return jsonify({"message": "Candidature introuvable."}), 404
    return jsonify({"message": "Candidature supprimee."})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
