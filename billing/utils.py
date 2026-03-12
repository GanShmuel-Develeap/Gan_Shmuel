import mysql.connector
import os
from datetime import datetime
import api_client
import pandas as pd

# Folder where Excel rate files are expected to exist
IN_FOLDER = "/in"

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

def get_weight_connection():#remove?
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
        cursor.close(); conn.close()
        return None, "Provider already exists"
    cursor.execute("INSERT INTO Provider (name) VALUES (%s)", (name,))
    conn.commit()
    provider_id = cursor.lastrowid
    cursor.close(); conn.close()
    return provider_id, None

def get_providers():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)  # dict במקום tuple
    cursor.execute("SELECT id, name FROM Provider")
    providers = cursor.fetchall()
    cursor.close()
    conn.close()
    return providers


def list_trucks():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT t.id, t.provider_id, p.name AS provider_name FROM Trucks t LEFT JOIN Provider p ON t.provider_id = p.id ORDER BY t.id")
        rows = cursor.fetchall()
        cursor.close(); conn.close()
        return rows, None
    except Exception as e:
        return None, str(e)


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
    Fetch truck details and its weighing sessions.
    Args:
        truck_id (str): Truck identifier.
        from_dt (str, optional): Start of time range ('yyyymmddhhmmss').
        to_dt (str, optional): End of time range ('yyyymmddhhmmss').

    Returns:
        dict: Truck info with 'id', 'tara', and 'sessions', or error message if not found.
    """
    # 1. Verify truck exists in billing DB
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM Trucks WHERE id = %s", (truck_id,))
    truck = cursor.fetchone()
    cursor.close()
    conn.close()

    if not truck:
        return None, "Truck not found"

    # 2. Default date range
    now = datetime.now()
    t1 = _parse_dt(from_dt) if from_dt else now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    t2 = _parse_dt(to_dt) if to_dt else now

    params = {
        "from": t1.strftime("%Y%m%d%H%M%S"),
        "to": t2.strftime("%Y%m%d%H%M%S")
    }

    # 3. Call Weight API
    data, err = api_client.get_item(truck_id, params=params)
    if err:
        return None, "Truck not found in weight system"

    
    return {
        "id": truck_id,
        "tara": data.get("tara"),
        "sessions": data.get("sessions", [])
    }, None


# ---- Bill ---- 




def get_provider_name(id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM Provider WHERE id = %s", (id,))
    name = cursor.fetchone()
    if name:
        cursor.close()
        conn.close()
        return name[0]
    cursor.close()
    conn.close()
    return False

def get_valid_trucks(weight_list, provider_id):
    #Extract all unique truck IDs from your dictionary list

    #for every item in weight_list if truck['truck_id'] is not already in the set enter it this ensures unique truck ids
    input_ids = list(set(item['truck_id'].upper() for item in weight_list))
    
    if not input_ids:
        return []

    valid_ids_from_db = set()
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        #Build the dynamic 'IN' clause placeholders (%s, %s, %s...)
        placeholders = ', '.join(['%s'] * len(input_ids))
        query = f"""
            SELECT id 
            FROM Trucks 
            WHERE provider_id = %s AND id IN ({placeholders})
        """
        
        #Execute in 1 trip
        #Pass provider_id first, then the list of IDs
        cursor.execute(query, [provider_id] + input_ids)
        
        # Store results in a set for lightning-fast cross-referencing

        # for every row in cursor.fetchall() get the first item row[0] 'id' 
        valid_ids_from_db = {row[0].upper() for row in cursor.fetchall()}
        
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

    #cross-reference: Filter the original list

    # We only keep the dictionary if its 'id' exists in our 'valid_ids_from_db' set

    #for every truck in weight_list if truck['id'] is in valid_ids_from_db enter it to the list valid_trucks
    valid_trucks = [
        truck for truck in weight_list 
        if truck['truck_id'].upper() in valid_ids_from_db
    ]
    
    return valid_trucks

def get_unique_trucks(valid_trucks):
    
    #Extract IDs and convert to a set to remove duplicates

    # get every unique truck in valid_trucks and enter it to dict
    unique_trucks = {truck['truck_id'] for truck in valid_trucks}
    
    #Convert back to a list
    unique_trucks = list(unique_trucks)
    
    #Return the unique_trucks
    return unique_trucks

def get_rates_for_provider(id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        query = """
            SELECT * 
            FROM Rates
        """

        cursor.execute(query)

        rates = {}

        for row in cursor.fetchall():
            product = row['product_name']
            scope = row['scope']
            rate = row['rate']

            if scope is None:
                if product not in rates: # Only set default if not already set by an ID
                    rates[product] = rate
            elif scope == id:
                rates[product] = rate # Override whatever is there

    except Exception:
        return None ,'error db connection failed'

    finally:
        cursor.close(); conn.close()

    # Return number of inserted rows
    return rates, None

def get_bill_data(truck_id: str, from_dt=None, to_dt=None):

    id = truck_id

    name = get_provider_name(id)
    if not name:
        return None, "Provider not found"

    now = datetime.now()
    from_time = _parse_dt(from_dt) if from_dt else now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    to_time = _parse_dt(to_dt) if to_dt else now

    params = {
        "from": from_time.strftime("%Y%m%d%H%M%S"),
        "to": to_time.strftime("%Y%m%d%H%M%S"),
        "filter":"out"
    }

    weight_data, err = api_client.get_weights(params=params)
    if err:
        return None, "Error accessing weight server"

    valid_trucks = get_valid_trucks(weight_data,id)

    unique_trucks = get_unique_trucks(valid_trucks)

    #Get the count
    truckCount = len(unique_trucks)
    sessionCount = 0
    total = 0

    sessionCount = len(valid_trucks)

    unique_products = {}
    product_index = 0
    products = []

    #get rates for all produce in a dict
    rates,err = get_rates_for_provider(id)
    if err:
        return None,err


    for truck in valid_trucks:
        if truck['neto'] == 'na':
            #add new addition to products with untracked neto
            if truck['produce'] + '_untracked_neto' not in unique_products:
                unique_products[truck['produce'] + '_untracked_neto'] = product_index
                product_index += 1
                
                rate = rates.get(truck['produce'], 0)
                pay = 'na'
                products.append({
                    'product': truck['produce']+'_untracked_neto',
                    'count': 1,#first trip
                    'amount': 'na',
                    'rate': rate,
                    'pay': pay
                    })
            else:
                temp_index = unique_products[truck['produce'] + '_untracked_neto']

                products[temp_index]['count'] += 1

        #add new addition to products with tracked neto
        elif truck['produce'] not in unique_products:
            unique_products[truck['produce']] = product_index
            product_index += 1
            
            rate = rates.get(truck['produce'], 0)
            pay = rate * truck['neto'] 
            total += pay
            products.append({
                'product': truck['produce'],
                'count': 1,#first trip
                'amount': truck['neto'],
                'rate': rate,
                'pay': pay
                })
        #add data to products[temp_index]
        else:
            temp_index = unique_products[truck['produce']]

            pay = rates.get(truck['produce'], 0) * truck['neto']
            total += pay
            products[temp_index]['count'] += 1
            products[temp_index]['amount'] += truck['neto']
            products[temp_index]['pay'] += pay
            

    return {
        #provider_id from get_bill_data id paramater
        "id": id,

        #provider_name from get_provider_name return value
        "name": name,

        #time stamp "from" from get_bill_data t1 paramater
        "from": params['from'],

        #time stamp "to" from get_bill_data t2 paramater
        "to": params['to'],

        #unique truck count from get_bill_data inner calculation 
        "truckCount": truckCount,

        #session count for this provider from get_bill_data inner calculation
        "sessionCount": sessionCount,

        #unique product list from get_bill_data inner calculation 
        "products": products,

        #total pay from get_bill_data inner calculation 
        "total": total
    },None




