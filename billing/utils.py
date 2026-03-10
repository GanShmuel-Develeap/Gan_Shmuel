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

# ---- Rates ----

def _validate_rates(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure the Excel file contains data
    if df.empty:
        raise ValueError("Excel file contains no data rows")

    # Ensure required columns do not contain missing values
    for col in ["Product", "Rate"]:
        bad = df.index[df[col].isna()].tolist()
        if bad:
            raise ValueError(f"Missing {col} value in rows: {bad}")

    # Clean product names (convert to string and remove surrounding spaces)
    df["Product"] = df["Product"].astype(str).str.strip()

    # Convert Rate column to numeric values
    df["Rate"] = pd.to_numeric(df["Rate"], errors="coerce")

    # Detect non-numeric rates
    bad = df.index[df["Rate"].isna()].tolist()
    if bad:
        raise ValueError(f"Non-numeric Rate value in rows: {bad}")

    # Convert rate to integer
    df["Rate"] = df["Rate"].astype(int)

    # Helper function to normalize Scope values
    def parse_scope(val):
        # If empty or "All", treat as None (global scope)
        if pd.isna(val) or str(val).strip().lower() == "all":
            return None
        try:
            # Otherwise scope must be a provider id
            return int(val)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid Scope '{val}': must be 'All' or a numeric provider id")

    # Apply scope parsing to the column
    df["Scope"] = df["Scope"].apply(parse_scope)
    return df


def upload_rates(filename: str):

    file_path = os.path.join(IN_FOLDER, filename)

    if not os.path.isdir(IN_FOLDER):
        return None, "/in folder not found on server"

    # Validate file exists
    if not os.path.isfile(file_path):
        return None, f"File '{filename}' not found in /in folder"

    try:
        df = pd.read_excel(file_path, usecols=["Product", "Rate", "Scope"])
    except Exception as e:
        return None, f"Failed to read Excel file: {str(e)}"

    # Validate and clean the data
    df = _validate_rates(df)

    # Replace NaN with None so MySQL can accept NULL values
    df = df.astype(object).where(pd.notnull(df), None)

    # Convert dataframe rows into tuples for batch insert
    rows = list(df[["Product", "Rate", "Scope"]].itertuples(index=False, name=None))

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Remove existing rates before inserting the new set
        cursor.execute("DELETE FROM Rates")

        # Insert all rows at once
        cursor.executemany(
            "INSERT INTO Rates (product_name, rate, scope) VALUES (%s, %s, %s)", rows
        )

        conn.commit()

    except Exception:
        # Rollback if any error occurs
        conn.rollback()
        raise

    finally:
        cursor.close(); conn.close()

    # Return number of inserted rows
    return len(rows), None


def get_rates_file_path():
    # Find all Excel files in the /in folder
    files = []

    for f in os.listdir(IN_FOLDER):
        if f.endswith(".xlsx"):
            full_path = os.path.join(IN_FOLDER, f)
            files.append(full_path)

    if not files:
        return None, "No rates files found in /in folder"

    # Select the most recently modified file
    latest = max(files, key=os.path.getmtime)

    return latest, None

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
