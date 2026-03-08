import mysql.connector
import os

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
# ---- Health ----

def health_check():
    try:
        conn = get_connection()
        if conn.is_connected():
            conn.close()
            return True
        return False
    except:
       return False

# ---- Provider ----

def create_provider(name: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM Provider WHERE name = %s", (name,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return None, "Provider already exists"

    cursor.execute("INSERT INTO Provider (name) VALUES (%s)", (name,))
    conn.commit()
    provider_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return provider_id, None


def update_provider(provider_id: int, name: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM Provider WHERE id = %s", (provider_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return False, "Provider not found"

    cursor.execute("SELECT id FROM Provider WHERE name = %s AND id != %s", (name, provider_id))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return False, "Provider name already taken"

    cursor.execute("UPDATE Provider SET name = %s WHERE id = %s", (name, provider_id))
    conn.commit()
    cursor.close()
    conn.close()
    return True, None