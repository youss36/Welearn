import re
import mysql.connector
from pypdf import PdfReader

DEGREE_MARKS = ("Bachelor", "Master", "Associate")
FOOTER_MARKS = ["we learn", "info@welearn.com", "+90 535 227 30 94", "we learn | info@welearn.com"]

UNIVERSITIES = [
    {"pdf": r"C:\Users\SKYMIL\Downloads\programs (1).pdf", "name": "Istinye University"},
    {"pdf": r"C:\Users\SKYMIL\Downloads\programs (29).pdf", "name": "Istanbul Okan University"},
    {"pdf": r"C:\Users\SKYMIL\Downloads\programs (3).pdf", "name": "Uskudar University"},
    {"pdf": r"C:\Users\SKYMIL\Downloads\programs (30).pdf", "name": "Istanbul Aydin University"},
    {"pdf": r"C:\Users\SKYMIL\Downloads\programs (8).pdf", "name": "Bahcesehir University"},
    {"pdf": r"C:\Users\SKYMIL\Downloads\programs (17).pdf", "name": "Istanbul Medipol University"},
]


def extract_lines(path):
    reader = PdfReader(path)
    lines = []
    for page in reader.pages:
        text = page.extract_text() or ""
        for raw in text.splitlines():
            line = raw.replace("\u202a", "").replace("\u202c", "").strip()
            if line:
                lines.append(line)
    return lines


def parse_programs(lines):
    programs = []
    for i in range(len(lines) - 1):
        name = lines[i]
        meta = lines[i + 1]
        if any(mark in name.lower() for mark in FOOTER_MARKS):
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
            elif any(mark in line.lower() for mark in FOOTER_MARKS):
                break
            elif "|" in line and any(d in line for d in DEGREE_MARKS):
                break
        programs.append({"name": name, "meta": meta, "faculty": faculty, "offer_price": offer_price})
    return programs


def build_available_programs(programs):
    rows = []
    for p in programs:
        parts = [part.strip() for part in p["meta"].split("|") if part.strip()]
        degree = parts[0] if parts else ""
        duration = parts[1] if len(parts) > 1 else ""
        language = parts[2] if len(parts) > 2 else ""
        fee = f" - {p['offer_price']}$/an" if p["offer_price"] else ""
        rows.append(f"- {p['name']} ({degree} | {duration} | {language}){fee}")
    return "\n".join(rows)


def main():
    conn = mysql.connector.connect(
        host="localhost", user="root", password="", port=3307,
        database="welearn_crm", charset="utf8mb4", collation="utf8mb4_unicode_ci",
    )
    cursor = conn.cursor()

    for uni in UNIVERSITIES:
        lines = extract_lines(uni["pdf"])
        programs = parse_programs(lines)
        available_programs = build_available_programs(programs)

        cursor.execute("SELECT COUNT(*) FROM universities WHERE name = %s", (uni["name"],))
        exists = cursor.fetchone()[0]
        if exists:
            cursor.execute(
                "UPDATE universities SET city=%s, country=%s, available_programs=%s WHERE name=%s",
                ("Istanbul", "Turquie", available_programs, uni["name"]),
            )
            status = "mise a jour"
        else:
            cursor.execute(
                """INSERT INTO universities (name, city, country, available_programs)
                   VALUES (%s, %s, %s, %s)""",
                (uni["name"], "Istanbul", "Turquie", available_programs),
            )
            status = "ajoutee"
        print(f"{uni['name']}: {len(programs)} programmes ({status})")

    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
