import mysql.connector
import os
import pandas as pd

IN_FOLDER = "/in"


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )


# ---- Provider ----

def create_provider(name: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Provider WHERE name = %s", (name,))
    if cursor.fetchone():
        cursor.close(); conn.close()
        return None, "Provider already exists"
    cursor.execute("INSERT INTO Provider (name) VALUES (%s)", (name,))
    conn.commit()
    provider_id = cursor.lastrowid
    cursor.close(); conn.close()
    return provider_id, None


def update_provider(provider_id: int, name: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Provider WHERE id = %s", (provider_id,))
    if not cursor.fetchone():
        cursor.close(); conn.close()
        return False, "Provider not found"
    cursor.execute("SELECT id FROM Provider WHERE name = %s AND id != %s", (name, provider_id))
    if cursor.fetchone():
        cursor.close(); conn.close()
        return False, "Provider name already taken"
    cursor.execute("UPDATE Provider SET name = %s WHERE id = %s", (name, provider_id))
    conn.commit()
    cursor.close(); conn.close()
    return True, None


# ---- Rates ----

def _validate_rates(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        raise ValueError("Excel file contains no data rows")

    for col in ["Product", "Rate"]:
        bad = df.index[df[col].isna()].tolist()
        if bad:
            raise ValueError(f"Missing {col} value in rows: {bad}")

    df["Product"] = df["Product"].astype(str).str.strip()
    df["Rate"] = pd.to_numeric(df["Rate"], errors="coerce")
    bad = df.index[df["Rate"].isna()].tolist()
    if bad:
        raise ValueError(f"Non-numeric Rate value in rows: {bad}")
    df["Rate"] = df["Rate"].astype(int)

    def parse_scope(val):
        if pd.isna(val) or str(val).strip().lower() == "all":
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid Scope '{val}': must be 'All' or a numeric provider id")

    df["Scope"] = df["Scope"].apply(parse_scope)
    return df


def upload_rates(filename: str):
    file_path = os.path.join(IN_FOLDER, filename)

    if not os.path.isdir(IN_FOLDER):
        return None, "/in folder not found on server"
    if not os.path.isfile(file_path):
        return None, f"File '{filename}' not found in /in folder"

    try:
        df = pd.read_excel(file_path, usecols=["Product", "Rate", "Scope"])
    except Exception as e:
        return None, f"Failed to read Excel file: {str(e)}"

    df = _validate_rates(df)

    df = df.astype(object).where(pd.notnull(df), None)

    rows = list(df[["Product", "Rate", "Scope"]].itertuples(index=False, name=None))
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Rates")
        cursor.executemany(
            "INSERT INTO Rates (product_name, rate, scope) VALUES (%s, %s, %s)", rows
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close(); conn.close()

    return len(rows), None


def get_rates_file_path():
    files = [
        os.path.join(IN_FOLDER, f)
        for f in os.listdir(IN_FOLDER)
        if f.endswith(".xlsx")
    ]
    if not files:
        return None, "No rates files found in /in folder"
    latest = max(files, key=os.path.getmtime)
    return latest, None