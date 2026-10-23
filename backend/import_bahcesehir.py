import re
import mysql.connector
from pypdf import PdfReader

PDF_PATH = r"C:\Users\SKYMIL\Downloads\programs.pdf"

reader = PdfReader(PDF_PATH)
lines = []
for page in reader.pages:
    text = page.extract_text() or ""
    for raw in text.splitlines():
        line = raw.replace("\u202a", "").replace("\u202c", "").strip()
        if line:
            lines.append(line)

FOOTER_MARKS = ["WE LEARN", "info@welearn.com", "+90 535 227 30 94", "WE LEARN | info@welearn.com"]
DEGREE_MARKS = ("Bachelor", "Master", "Associate", "Doctorate")
programs = []
for i in range(len(lines) - 1):
    name = lines[i]
    meta = lines[i + 1]
    if any(mark.lower() in name.lower() for mark in FOOTER_MARKS):
        continue
    if "|" not in meta or not any(d in meta for d in DEGREE_MARKS):
        continue
    faculty = ""
    offer_price = ""
    for line in lines[i + 2:]:
        if line.lower().startswith("faculty"):
            faculty = re.sub(r"^faculty\s*:?\s*", "", line, flags=re.I)
        elif line.lower().startswith("offer price"):
            m = re.search(r"[\d.,]+", line)
            offer_price = m.group(0).replace(",", "") if m else ""
        elif any(mark.lower() in line.lower() for mark in FOOTER_MARKS):
            break
        elif "|" in line and any(d in line for d in DEGREE_MARKS):
            break
    programs.append({"name": name, "meta": meta, "faculty": faculty, "offer_price": offer_price})

rows = []
for p in programs:
    parts = [part.strip() for part in p["meta"].split("|") if part.strip()]
    degree = parts[0] if parts else ""
    duration = parts[1] if len(parts) > 1 else ""
    language = " | ".join(parts[2:]) if len(parts) > 2 else ""
    fee = f" - {p['offer_price']}$/an" if p["offer_price"] else ""
    rows.append(f"- {p['name']} ({degree} | {duration} | {language}){fee}")

available_programs = "\n".join(rows)
uni_name = "Bahcesehir University"
city = "Istanbul"
country = "Turquie"

conn = mysql.connector.connect(
    host="localhost", user="root", password="", port=3307,
    database="welearn_crm", charset="utf8mb4", collation="utf8mb4_unicode_ci",
)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM universities WHERE name = %s", (uni_name,))
if cursor.fetchone()[0]:
    cursor.execute(
        "UPDATE universities SET city=%s, country=%s, available_programs=%s WHERE name=%s",
        (city, country, available_programs, uni_name),
    )
    print("Universite mise a jour.")
else:
    cursor.execute(
        """INSERT INTO universities (name, city, country, available_programs)
           VALUES (%s, %s, %s, %s)""",
        (uni_name, city, country, available_programs),
    )
    print("Universite ajoutee.")
conn.commit()
print(f"Total programmes importes: {len(programs)}")
cursor.close()
conn.close()
