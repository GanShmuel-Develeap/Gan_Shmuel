from db import get_conn
from datetime import datetime
import mysql.connector
from mysql.connector import Error

def submit_weight_transaction(direction, truck, containers, bruto, produce):
    """
    Submit a weight transaction to the database.

    Args:
        direction (str): in/out/none
        truck (str): truck license or 'na'
        containers (str): comma-delimited container ids (optional for OUT)
        bruto (int): gross weight
        produce (str): produce type or 'na'

    Returns:
        dict: {'status': 'success'|'error', 'message': str, 'id': str or None, ...}
    """
    try:
        # Validate inputs
        if not all([direction, bruto]):
            return {
                'status': 'error',
                'message': 'Missing required fields: direction, bruto'
            }

        # For IN and NONE, containers are required
        if direction in ['in', 'none'] and not containers:
            return {
                'status': 'error',
                'message': 'Containers are required for IN and NONE directions'
            }

        # Default truck to 'na' if empty
        truck = truck or 'na'
        
        # Default containers to empty string if not provided
        containers = containers or ''

        # Convert inputs to integers
        try:
            bruto = int(bruto)
        except ValueError:
            return {
                'status': 'error',
                'message': 'Bruto must be a number'
            }

        # Default produce to 'na' if empty
        produce = produce or 'na'

        # Handle direction logic and calculate truckTara and neto
        if direction == 'out':
            # For OUT: weight input is truckTara, bruto is 0
            truckTara = bruto
            bruto = 0
            neto = 'na'  # Can't calculate without knowing actual bruto
        else:
            # For IN and NONE: weight input is bruto, truckTara is 0
            truckTara = 0
            # Calculate neto = bruto - truckTara - sum(container_taras)
            neto = calculate_neto(bruto, truckTara, containers)

        # Insert into database
        conn = get_conn()
        if not conn:
            return {
                'status': 'error',
                'message': 'Database connection failed'
            }

        try:
            cur = conn.cursor()
            query = """
                INSERT INTO transactions
                (datetime, direction, truck, containers, bruto, truckTara, neto, produce)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Convert neto to int for DB storage, use 0 if 'na'
            neto_db = 0 if neto == 'na' else neto
            
            values = (
                datetime.now(),
                direction,
                truck,
                containers,
                bruto,
                truckTara,
                neto_db,
                produce
            )
            cur.execute(query, values)
            conn.commit()
            transaction_id = cur.lastrowid
            cur.close()

            # Build response according to API spec
            response_data = {
                'id': str(transaction_id),
                'truck': truck,
                'bruto': bruto,
                'neto': neto
            }
            
            # Only include truckTara for OUT direction
            if direction == 'out':
                response_data['truckTara'] = truckTara

            return {
                'status': 'success',
                'message': 'Transaction recorded successfully',
                **response_data
            }

        except Error as e:
            print(f"Error inserting transaction: {e}")
            return {
                'status': 'error',
                'message': f'Database error: {str(e)}'
            }
        finally:
            if conn.is_connected():
                conn.close()

    except Exception as e:
        print(f"Unexpected error: {e}")
        return {
            'status': 'error',
            'message': f'Unexpected error: {str(e)}'
        }


def calculate_neto(bruto, truckTara, containers_str):
    """
    Calculate neto weight: bruto - truckTara - sum(container_taras)
    Returns 'na' if any container tara is unknown.
    """
    try:
        neto = bruto - truckTara
        
        if containers_str:
            container_ids = [c.strip() for c in containers_str.split(',') if c.strip()]
            
            for container_id in container_ids:
                container_tara = get_container_tara(container_id)
                if container_tara is None:
                    # Unknown tara for this container
                    return 'na'
                neto -= container_tara
        
        return neto
    except Exception as e:
        print(f"Error calculating neto: {e}")
        return 'na'


def get_container_tara(container_id):
    """
    Look up container tara weight from containers_registered table.
    Returns the weight or None if not found.
    """
    conn = get_conn()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        query = "SELECT weight FROM containers_registered WHERE container_id = %s"
        cur.execute(query, (container_id,))
        result = cur.fetchone()
        cur.close()
        return result[0] if result else None
    except Error as e:
        print(f"Error querying container tara: {e}")
        return None
    finally:
        if conn.is_connected():
            conn.close()
