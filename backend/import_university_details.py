import json
import re
import mysql.connector

JSON_PATH = r"C:\Users\SKYMIL\AppData\Local\Temp\opencode\studysehir\university_details.json"

details = json.load(open(JSON_PATH, encoding="utf-8"))

conn = mysql.connector.connect(
    host="localhost", user="root", password="", port=3307,
    database="welearn_crm", charset="utf8mb4", collation="utf8mb4_unicode_ci",
)
cursor = conn.cursor()

NEW_COLUMNS = {
    "logo_url": "VARCHAR(500) DEFAULT NULL",
    "thumbnail_url": "VARCHAR(500) DEFAULT NULL",
    "background_url": "VARCHAR(500) DEFAULT NULL",
    "district": "VARCHAR(120) DEFAULT NULL",
    "description": "LONGTEXT DEFAULT NULL",
}
cursor.execute("SHOW COLUMNS FROM universities")
existing_cols = {row[0] for row in cursor.fetchall()}
for col, definition in NEW_COLUMNS.items():
    if col not in existing_cols:
        cursor.execute(f"ALTER TABLE universities ADD COLUMN {col} {definition}")
        print(f"Colonne ajoutee: {col}")
conn.commit()


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


cursor.execute("SELECT id, name FROM universities")
db_unis = {norm(name): (id_, name) for id_, name in cursor.fetchall()}

updated = 0
missing = []
for slug, d in details.items():
    match = db_unis.get(norm(d["name"]))
    if not match:
        missing.append(d["name"])
        continue
    city = d["city"].capitalize() if d["city"] else ""
    district = d["district"].capitalize() if d["district"] else ""
    cursor.execute(
        """UPDATE universities
           SET logo_url=%s, thumbnail_url=%s, background_url=%s,
               description=%s, district=%s, city=COALESCE(NULLIF(%s,''), city)
           WHERE id=%s""",
        (d["logo_url"], d["thumbnail_url"], d["background_url"],
         d["description_html"], district, city, match[0]),
    )
    updated += 1

conn.commit()
print(f"Mises a jour: {updated}")
if missing:
    print("Sans correspondance:", missing)

cursor.execute("""SELECT name, city, district, LEFT(logo_url, 60), LENGTH(description)
                  FROM universities WHERE description IS NOT NULL LIMIT 5""")
for r in cursor.fetchall():
    print(r)
cursor.close()
conn.close()
