from db import get_conn
from datetime import datetime
import mysql.connector
from mysql.connector import Error

def submit_weight_transaction(direction, truck, containers, bruto, unit, produce):
    """
    Submit a weight transaction to the database.

    Args:
        direction (str): in/out/none
        truck (str): truck license or 'na'
        containers (str): comma-delimited container ids (optional for OUT)
        bruto (int): gross weight
        unit (str): unit of weight (kg/lbs)
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

        # Calculate session_id according to timestamp
        timestamp_str = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Connect to DB to handle direction logic
        conn = get_conn()
        if not conn:
            return {
                'status': 'error',
                'message': 'Database connection failed'
            }

        try:
            cur = conn.cursor(dictionary=True)
            if direction in ['in', 'none']:
                session_id = timestamp_str
            elif direction == 'out':
                if truck and truck != 'na':
                    query = "SELECT session_id FROM transactions WHERE truck = %s AND direction = 'in' ORDER BY datetime DESC LIMIT 1"
                    cur.execute(query, (truck,))
                    row = cur.fetchone()
                    if row and row['session_id']:
                        session_id = row['session_id']
                    else:
                        cur.close()
                        conn.close()
                        return {
                            'status': 'error',
                            'message': 'No prior IN transaction found for this truck'
                        }
                else:
                    cur.close()
                    conn.close()
                    return {
                        'status': 'error',
                        'message': 'Truck required for OUT direction'
                    }
            else:
                cur.close()
                conn.close()
                return {
                    'status': 'error',
                    'message': 'Invalid direction'
                }
            cur.close()
        except Error as e:
            if conn.is_connected():
                conn.close()
            return {
                'status': 'error',
                'message': f'Database error: {str(e)}'
            }

        # Handle direction logic
        if direction == 'out':
            # For OUT: weight input is truckTara
            truckTara = bruto

            # For OUT transactions, 'neto' is not calculated at the point of insertion.
            # It is a session-level property. We store 0 in the transaction record.
            neto_db = 0
        else:
            # For IN and NONE: weight input is bruto, truckTara is always 0
            truckTara = 0
            # For IN/NONE, neto is not calculated, store as 0 (displayed as 'na')
            neto_db = 0

        # We already have a database connection


        try:
            cur = conn.cursor()
            query = """
                INSERT INTO transactions
                (datetime, direction, truck, containers, bruto, truckTara, neto, produce, unit, session_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                datetime.now(),
                direction,
                truck,
                containers,
                bruto if direction != 'out' else 0,  # For OUT, bruto is stored as 0
                truckTara,
                neto_db,
                produce,
                unit,
                session_id
            )
            cur.execute(query, values)
            conn.commit()
            transaction_id = cur.lastrowid
            cur.close()

            if direction == 'out':
                # Reuse session logic to calculate neto and get full session details
                session_info = get_session_info(str(session_id))
                if session_info['status'] == 'success':
                    sess_data = session_info['data']
                    summary = sess_data.get('session_summary', {})
                    
                    # For OUT, spec requires: id, truck, bruto (IN weight), truckTara (OUT weight), neto
                    response_data = {
                        'id': str(session_id),
                        'truck': truck,
                        'bruto': summary.get('in_weight', 0),
                        'truckTara': summary.get('out_weight', bruto),
                        'neto': summary.get('calculated_neto', 'na'),
                    }
                else:
                    # Fallback if session lookup fails
                    response_data = {
                        'id': str(session_id),
                        'truck': truck,
                        'bruto': 0,
                        'truckTara': bruto,
                        'neto': 'na',
                    }
            else:
                # IN and NONE
                response_data = {
                    'id': str(session_id),
                    'truck': truck,
                    'bruto': bruto,
                }

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


def get_session_info(session_id):
    """
    Get session information by session ID.
    Returns session data with all transactions.
    For sessions with both IN and OUT, neto is calculated as:
    neto = IN.bruto - OUT.truckTara - sum(container_taras)
    
    Args:
        session_id (str): Session ID (truck_YYYYMMDD or na_timestamp)
    
    Returns:
        dict: {'status': 'success'|'error', 'data': session_data or None}
    """
    conn = get_conn()
    if not conn:
        return {
            'status': 'error',
            'message': 'Database connection failed'
        }
    
    try:
        cur = conn.cursor(dictionary=True)
        
        # Get all transactions for this session
        query = """
            SELECT id, datetime, direction, truck, containers, bruto, truckTara, neto,
                   produce, unit, session_id
            FROM transactions 
            WHERE session_id = %s 
            ORDER BY datetime ASC
        """
        cur.execute(query, (session_id,))
        transactions = cur.fetchall()
        
        if not transactions:
            return {
                'status': 'error',
                'message': 'Session not found'
            }
        
        # Find IN and OUT transactions
        in_tx = next((tx for tx in transactions if tx['direction'] == 'in'), None)
        out_tx = next((tx for tx in transactions if tx['direction'] == 'out'), None)
        
        # Calculate neto only if both IN and OUT exist
        calculated_neto = 'na'
        if in_tx and out_tx:
            # neto = IN.bruto - OUT.truckTara - sum(container_taras)
            # IN.bruto is the total weight in, OUT.truckTara is the total weight out
            container_taras = 0
            can_calculate = True
            if in_tx['containers']:
                container_ids = [c.strip() for c in in_tx['containers'].split(',') if c.strip()]
                for container_id in container_ids:
                    tara = get_container_tara(container_id)
                    if tara is not None:
                        container_taras += tara
                    else:
                        # Can't calculate if any container tara is unknown
                        can_calculate = False
                        break
            
            if can_calculate:
                try:
                    calculated_neto = str(in_tx['bruto'] - out_tx['truckTara'] - container_taras)
                except:
                    calculated_neto = 'na'
        
        # Build session response
        session_data = {
            'session_id': session_id,
            'truck': transactions[0]['truck'],
            'transactions': []
        }
        
        # Add each transaction in the response (IN and OUT all return neto='na' individually)
        for tx in transactions:
            tx_data = {
                'id': str(tx['id']),
                'truck': tx['truck'],
                'bruto': tx['bruto'],
                'neto': 'na',  # Individual transactions always show neto as 'na'
                'unit': tx['unit'],
                'direction': tx['direction'],
                'datetime': tx['datetime'].isoformat() if tx['datetime'] else None
            }
            
            session_data['transactions'].append(tx_data)
        
        # Add calculated neto at session level if both IN and OUT exist
        if in_tx and out_tx:
            session_data['neto'] = calculated_neto
            session_data['session_summary'] = {
                'in_weight': in_tx['bruto'],
                'out_weight': out_tx['truckTara'],
                'calculated_neto': calculated_neto
            }
        
        return {
            'status': 'success',
            'data': session_data
        }
        
    except Error as e:
        print(f"Error querying session: {e}")
        return {
            'status': 'error',
            'message': f'Database error: {str(e)}'
        }
    finally:
        if conn.is_connected():
            conn.close()
