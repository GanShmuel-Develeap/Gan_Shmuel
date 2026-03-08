import mysql.connector
import os
import pandas as pd

# Folder where Excel rate files are expected to exist
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
    files = [
        os.path.join(IN_FOLDER, f)
        for f in os.listdir(IN_FOLDER)
        if f.endswith(".xlsx")
    ]

    if not files:
        return None, "No rates files found in /in folder"

    # Select the most recently modified file
    latest = max(files, key=os.path.getmtime)

    return latest, None