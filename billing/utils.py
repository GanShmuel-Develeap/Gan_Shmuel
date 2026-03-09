import mysql.connector
import os
from datetime import datetime

def get_bill_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "billdb")
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

def get_weight_connection():
    return mysql.connector.connect(
        host=os.getenv("WEIGHT_DB_HOST", os.getenv("DB_HOST")),
        user=os.getenv("WEIGHT_DB_USER", os.getenv("DB_USER")),
        password=os.getenv("WEIGHT_DB_PASSWORD", os.getenv("DB_PASSWORD")),
        database=os.getenv("WEIGHT_DB_NAME", "weight")
    )

# Keep backward-compat alias
def get_connection():
    return get_bill_connection()

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

# ---- Truck ----

def create_truck(truck_id: str, provider_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM Provider WHERE id = %s", (provider_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return False, "Provider not found"

    cursor.execute("SELECT id FROM Trucks WHERE id = %s", (truck_id,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return False, "Truck already exists"

    cursor.execute("INSERT INTO Trucks (id, provider_id) VALUES (%s, %s)", (truck_id, provider_id))
    conn.commit()
    cursor.close()
    conn.close()
    return True, None


def update_truck(truck_id: str, provider_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM Trucks WHERE id = %s", (truck_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return False, "Truck not found"

    cursor.execute("SELECT id FROM Provider WHERE id = %s", (provider_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return False, "Provider not found"

    cursor.execute("UPDATE Trucks SET provider_id = %s WHERE id = %s", (provider_id, truck_id))
    conn.commit()
    cursor.close()
    conn.close()
    return True, None


def _parse_dt(dt_str):
    """Parse yyyymmddhhmmss string to datetime."""
    return datetime.strptime(dt_str, "%Y%m%d%H%M%S")


def get_truck(truck_id: str, from_dt=None, to_dt=None):
    """
    Returns truck info from billing DB + sessions from weight DB.
    from_dt, to_dt: optional datetime strings (yyyymmddhhmmss).
    Defaults: from = 1st of current month 000000, to = now.
    """
    # 1. Verify truck exists in billing DB
    bill_conn = get_bill_connection()
    bill_cursor = bill_conn.cursor(dictionary=True)
    bill_cursor.execute("SELECT id FROM Trucks WHERE id = %s", (truck_id,))
    truck = bill_cursor.fetchone()
    bill_cursor.close()
    bill_conn.close()

    if not truck:
        return None, "Truck not found"

    # 2. Apply defaults for date range
    now = datetime.now()
    t1 = _parse_dt(from_dt) if from_dt else now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    t2 = _parse_dt(to_dt) if to_dt else now

    # 3. Fetch from weight DB
    weight_conn = get_weight_connection()
    weight_cursor = weight_conn.cursor(dictionary=True)

    # Sessions in range
    weight_cursor.execute(
        "SELECT id FROM transactions WHERE truck = %s AND datetime >= %s AND datetime <= %s",
        (truck_id, t1, t2)
    )
    sessions = [row["id"] for row in weight_cursor.fetchall()]

    # Last known tara (most recent truckTara across all time)
    weight_cursor.execute(
        """SELECT truckTara FROM transactions
           WHERE truck = %s AND truckTara IS NOT NULL
           ORDER BY datetime DESC LIMIT 1""",
        (truck_id,)
    )
    tara_row = weight_cursor.fetchone()
    tara = tara_row["truckTara"] if tara_row else None

    weight_cursor.close()
    weight_conn.close()

    return {"id": truck_id, "tara": tara, "sessions": sessions}, None