from db import get_conn
from datetime import datetime
import mysql.connector
from mysql.connector import Error

def submit_weight_transaction(direction, truck, containers, bruto, unit, produce, force=False):
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
        if not direction or bruto is None:
            return {
                'status': 'error',
                'message': 'Missing required fields: direction, bruto'
            }

        # 2. no change needed here; current IN behavior already covers this
        if direction in ['in', 'none'] and not containers:
            return {
                'status': 'error',
                'message': 'Containers are required for IN and NONE directions'
            }

        # 1. truck required for IN / OUT
        if direction in ['in', 'out'] and not (truck and str(truck).strip()):
            return {
                'status': 'error',
                'message': 'Truck is required for IN and OUT directions'
            }

        containers = containers or ''

        try:
            bruto = int(bruto)
        except (ValueError, TypeError):
            return {
                'status': 'error',
                'message': 'Bruto must be a number'
            }

        # 3. weight must be > 0
        if bruto <= 0:
            return {
                'status': 'error',
                'message': 'Weight must be greater than 0'
            }

        produce = produce or 'na'
        timestamp_str = datetime.now().strftime('%Y%m%d%H%M%S')

        conn = get_conn()
        if not conn:
            return {
                'status': 'error',
                'message': 'Database connection failed'
            }

        try:
            cur = conn.cursor(dictionary=True)
            prior_in = None

            if direction in ['in', 'none'] and truck and truck != 'na':
                query = """
                SELECT session_id FROM transactions 
                WHERE truck = %s AND direction IN ('in', 'none') 
                AND session_id NOT IN (SELECT session_id FROM transactions WHERE direction = 'out')
                ORDER BY datetime DESC LIMIT 1
                """
                cur.execute(query, (truck,))
                row = cur.fetchone()
                if row:
                    if not force:
                        cur.close()
                        conn.close()
                        return {
                            'status': 'error',
                            'message': 'Truck has an open session. Use force=true to overwrite.'
                        }
                    else:
                        delete_query = "DELETE FROM transactions WHERE session_id = %s"
                        cur.execute(delete_query, (row['session_id'],))
                        conn.commit()

            if direction in ['in', 'none']:
                session_id = f"{truck}_{timestamp_str}"
            elif direction == 'out':
                query = """
                SELECT session_id, bruto, produce
                FROM transactions
                WHERE truck = %s AND direction = 'in'
                ORDER BY datetime DESC
                LIMIT 1
                """
                cur.execute(query, (truck,))
                prior_in = cur.fetchone()
                if prior_in and prior_in['session_id']:
                    session_id = prior_in['session_id']
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
                    'message': 'Invalid direction'
                }

            if direction == 'out':
                check_query = "SELECT id FROM transactions WHERE session_id = %s AND direction = 'out'"
                cur.execute(check_query, (session_id,))
                if cur.fetchone():
                    if not force:
                        cur.close()
                        conn.close()
                        return {
                            'status': 'error',
                            'message': 'Session already has an OUT transaction. Use force=true to overwrite.'
                        }
                    else:
                        delete_query = "DELETE FROM transactions WHERE session_id = %s AND direction = 'out'"
                        cur.execute(delete_query, (session_id,))
                        conn.commit()

                in_bruto = int(prior_in['bruto'])

                # 4. OUT weight cannot be bigger than matching IN weight
                if bruto > in_bruto:
                    cur.close()
                    conn.close()
                    return {
                        'status': 'error',
                        'message': 'OUT weight cannot be greater than the matching IN weight'
                    }

            cur.close()
        except Error as e:
            if conn.is_connected():
                conn.close()
            return {
                'status': 'error',
                'message': f'Database error: {str(e)}'
            }

        if direction == 'out':
            # 5. incoming OUT weight is truckTara; bruto comes from matching IN
            truckTara = bruto
            bruto_db = int(prior_in['bruto'])

            # 6. OUT produce copied from matching IN
            produce_db = prior_in['produce'] or 'na'
            neto_db = 0
        else:
            truckTara = 0
            bruto_db = bruto
            produce_db = produce
            neto_db = 0

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
                bruto_db,
                truckTara,
                neto_db,
                produce_db,
                unit,
                session_id
            )
            cur.execute(query, values)
            conn.commit()
            transaction_id = cur.lastrowid
            cur.close()

            if direction == 'out':
                session_info = get_session_info(str(session_id))
                if session_info['status'] == 'success':
                    sess_data = session_info['data']
                    summary = sess_data.get('session_summary', {})

                    neto_val = summary.get('calculated_neto', 'na')
                    if neto_val != 'na':
                        try:
                            neto_val = int(neto_val)

                            update_cur = conn.cursor()
                            update_cur.execute("UPDATE transactions SET neto = %s WHERE id = %s", (neto_val, transaction_id))
                            conn.commit()
                            update_cur.close()
                        except:
                            pass

                    response_data = {
                        'id': str(transaction_id),
                        'truck': truck,
                        'bruto': bruto_db,
                        'truckTara': truckTara,
                        'neto': neto_val,
                    }
                else:
                    response_data = {
                        'id': str(transaction_id),
                        'truck': truck,
                        'bruto': bruto_db,
                        'truckTara': truckTara,
                        'neto': 'na',
                    }
            else:
                response_data = {
                    'id': str(transaction_id),
                    'truck': truck,
                    'bruto': bruto_db,
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


# def get_container_tara(container_id):
#     """
#     Look up container tara weight from containers_registered table.
#     Returns the weight or None if not found.
#     """
#     conn = get_conn()


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
                    calculated_neto = int(in_tx['bruto'] - out_tx['truckTara'] - container_taras)
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
