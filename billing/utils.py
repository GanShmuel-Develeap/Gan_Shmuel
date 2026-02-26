import mysql.connector
import os

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "mysql"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "root"),
        database=os.getenv("DB_NAME", "billing")
    )

# ---- Provider ----

def create_provider(name: str):
   
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO Provider (name) VALUES (%s)",
        (name,)
    )
    conn.commit()
    provider_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return provider_id


def get_all_providers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM Provider")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{"id": r[0], "name": r[1]} for r in rows]


