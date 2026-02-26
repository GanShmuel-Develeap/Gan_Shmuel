import os
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import mysql.connector
from mysql.connector import Error

app = Flask(__name__, template_folder='templates')
from flask import redirect, url_for

# Database connection configuration
def get_db_connection():
    """Establish MySQL database connection"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', 'password'),
            database=os.getenv('DB_NAME', 'weight_db')
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def get_truck_tara(truck_id):
    """Look up truck tara weight from containers_registered table"""
    connection = get_db_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        # Assuming truck_id might be stored as container_id in the table
        query = "SELECT weight FROM containers_registered WHERE container_id = %s"
        cursor.execute(query, (truck_id,))
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None
    except Error as e:
        print(f"Error querying truck tara: {e}")
        return None
    finally:
        if connection.is_connected():
            connection.close()


@app.route('/')
def root_redirect():
    """Redirect root to weight form"""
    return redirect(url_for('weight_form'))


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return ('OK', 200)


@app.route('/weight', methods=['GET'])
def weight_form():
    """Serve the weight form HTML"""
    return render_template('weight_form.html')


@app.route('/truck-tara/<truck_id>', methods=['GET'])
def truck_tara_lookup(truck_id):
    """Return tara weight for a given truck ID"""
    tara = get_truck_tara(truck_id)
    if tara is None:
        return jsonify({'truck': truck_id, 'tara': None}), 404
    return jsonify({'truck': truck_id, 'tara': tara})


@app.route('/weight', methods=['POST'])
def weight_submit():
    """Handle weight transaction form submission"""
    try:
        # Get form data
        direction = request.form.get('direction')
        truck = request.form.get('truck')
        containers = request.form.get('containers')
        produce = request.form.get('produce')
        bruto = request.form.get('bruto')

        # Validate required fields
        if not all([direction, truck, containers, bruto]):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields: direction, truck, containers, bruto'
            }), 400

        # Convert bruto to integer
        try:
            bruto = int(bruto)
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'Bruto weight must be a number'
            }), 400

        # Look up truck tara
        truck_tara = get_truck_tara(truck)
        if truck_tara is None:
            # If truck not found, set tara to 0 or return error based on business logic
            truck_tara = 0
            print(f"Warning: Truck {truck} not found in database, using tara=0")

        # Calculate neto weight
        neto = bruto - truck_tara

        # Insert into transactions table
        connection = get_db_connection()
        if not connection:
            return jsonify({
                'status': 'error',
                'message': 'Database connection failed'
            }), 500

        try:
            cursor = connection.cursor()
            query = """
                INSERT INTO transactions 
                (datetime, direction, truck, containers, bruto, truckTara, neto, produce)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                datetime.now(),
                direction,
                truck,
                containers,
                bruto,
                truck_tara,
                neto,
                produce if produce else None
            )
            cursor.execute(query, values)
            connection.commit()
            transaction_id = cursor.lastrowid
            cursor.close()

            return jsonify({
                'status': 'success',
                'message': 'Transaction recorded successfully',
                'transaction_id': transaction_id,
                'data': {
                    'datetime': datetime.now().isoformat(),
                    'direction': direction,
                    'truck': truck,
                    'containers': containers,
                    'bruto': bruto,
                    'truckTara': truck_tara,
                    'neto': neto,
                    'produce': produce
                }
            }), 201

        except Error as e:
            print(f"Error inserting transaction: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Database error: {str(e)}'
            }), 500
        finally:
            if connection.is_connected():
                connection.close()

    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}'
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

