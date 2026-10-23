import json
import re
import mysql.connector

JSON_PATH = r"C:\Users\SKYMIL\AppData\Local\Temp\opencode\studysehir\programs.json"

CYPRUS_MARK = "cyprus"
ANKARA_UNIS = {"ankara medipol university", "ostim teknilk university", "ted university"}

programs = json.load(open(JSON_PATH, encoding="utf-8"))

seen = set()
cleaned = []
for p in programs:
    key = (
        p["uni"].lower(),
        p["name"].lower(),
        p["degree"].lower(),
        p["duration"].lower(),
        p["language"].lower(),
        p["offer"],
    )
    if key in seen:
        continue
    seen.add(key)
    cleaned.append(p)
programs = cleaned
print(f"Programs apres deduplication: {len(programs)}")

by_uni = {}
for p in programs:
    by_uni.setdefault(p["uni"], []).append(p)


def fee_num(offer):
    m = re.search(r"[\d.,]+", offer)
    return m.group(0).replace(",", "") if m else ""


def build_available_programs(items):
    rows = []
    for p in items:
        fee = fee_num(p["offer"])
        fee_txt = f" - {fee}$/an" if fee else ""
        rows.append(
            f"- {p['name']} ({p['degree']} | {p['duration']} | {p['language']}){fee_txt}"
        )
    return "\n".join(rows)


def location_for(name):
    low = name.lower()
    if CYPRUS_MARK in low:
        return ("Cyprus", "Chypre")
    if low in ANKARA_UNIS:
        return ("Ankara", "Turquie")
    return ("Istanbul", "Turquie")


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


conn = mysql.connector.connect(
    host="localhost", user="root", password="", port=3307,
    database="welearn_crm", charset="utf8mb4", collation="utf8mb4_unicode_ci",
)
cursor = conn.cursor()
cursor.execute("SELECT id, name FROM universities")
existing = {norm(name): (id_, name) for id_, name in cursor.fetchall()}

added, updated = 0, 0
for uni_name, items in sorted(by_uni.items()):
    city, country = location_for(uni_name)
    available_programs = build_available_programs(items)

    match = existing.get(norm(uni_name))
    if match:
        cursor.execute(
            "UPDATE universities SET city=%s, country=%s, available_programs=%s WHERE id=%s",
            (city, country, available_programs, match[0]),
        )
        updated += 1
        status = "mise a jour"
    else:
        cursor.execute(
            """INSERT INTO universities (name, city, country, available_programs)
               VALUES (%s, %s, %s, %s)""",
            (uni_name, city, country, available_programs),
        )
        added += 1
        status = "ajoutee"
    print(f"{uni_name}: {len(items)} programmes ({status})")

conn.commit()
print(f"\nTotal: {len(by_uni)} universites | ajoutees: {added} | mises a jour: {updated}")
cursor.close()
conn.close()
