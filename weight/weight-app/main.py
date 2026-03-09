import os
from datetime import datetime
from flask import Flask, jsonify, render_template, request
from flask import Flask, jsonify, request
import json
import csv
import mysql.connector
from mysql.connector import Error
from mock_routes import test_bp
from db import get_conn
from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)
app.register_blueprint(test_bp)
print(app.url_map)

@app.get("/")
def home():
    return "Weight App"

@app.route('/health', methods=['GET'])
def get_health():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT NOW()")
    (now,) = cur.fetchone()

    cur.close()
    conn.close()

    return jsonify(mysql_time=str(now))


@app.route('/weight', methods=['GET'])
def get_all_transactions():
    now = datetime.now()
    t1 = request.args.get("from", now.strftime("%Y%m%d") + "000000")
    t2 = request.args.get("to", now.strftime("%Y%m%d%H%M%S"))
    f = request.args.get("filter", "in,out,none")

    t1 = datetime.strptime(t1, "%Y%m%d%H%M%S")
    t2 = datetime.strptime(t2, "%Y%m%d%H%M%S")
    directions = f.split(",")

    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    placeholders = ",".join(["%s"] * len(directions))
    cur.execute(
        f"""
        SELECT id, direction, truck, bruto, neto, unit, produce, containers
        FROM transactions
        WHERE datetime BETWEEN %s AND %s
        AND direction IN ({placeholders})
        ORDER BY id
        """,
        [t1, t2] + directions
    )
    rows = cur.fetchall()

    cur.execute("SELECT container_id, weight FROM containers_registered")
    container_rows = cur.fetchall()

    cur.close()
    conn.close()

    container_weights = {}
    for row in container_rows:
        container_weights[row["container_id"]] = row["weight"]

    return jsonify([
        {
            "id": row["id"],
            "direction": row["direction"],
            "truck_id": row["truck"],
            "bruto": row["bruto"],
            "neto": get_neto(row["containers"], row["neto"], row["unit"], container_weights),
            "produce": row["produce"],
            "containers": row["containers"].split(",") if row["containers"] else []
        }
        for row in rows
    ])


def get_neto(containers_str, neto, unit, container_weights):
    if not containers_str:
        if unit == "lbs" and neto is not None:
            return round(neto * 0.45359237)
        return neto

    for c in containers_str.split(","):
        if c not in container_weights or container_weights[c] is None:
            return "na"

    if unit == "lbs" and neto is not None:
        return round(neto * 0.45359237)

    return neto

@app.route('/containers', methods=['GET'])
def get_containers():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT container_id, weight, unit
        FROM containers_registered
        ORDER BY container_id
    """)

    rows = cur.fetchall()

@app.route('/weight-form', methods=['GET'])
def weight_form():
    """Serve the weight form HTML"""
    return render_template('weight_form.html')



@app.route('/weight-form', methods=['POST'])
def weight_submit():
    """Handle weight transaction form submission"""
    # Get form data
    direction = request.form.get('direction')
    truck = request.form.get('truck')
    containers = request.form.get('containers')
    bruto = request.form.get('bruto')
    unit = request.form.get('unit', 'kg')
    produce = request.form.get('produce') or 'na'

    # Call the service function
    result = submit_weight_transaction(direction, truck, containers, bruto, unit, produce)

    # Return appropriate response
    if result['status'] == 'success':
        return jsonify(result), 201
    else:
        return jsonify(result), 400


@app.route('/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session information by session ID"""
    result = get_session_info(session_id)
    
    if result['status'] == 'success':
        return jsonify(result['data']), 200
    else:
        return jsonify(result), 404


@app.route('/batch-weight', methods=['POST'])
def batch_weight():
    filename = request.values.get('file')
    print(f"Received batch request for file: {filename}")
    if not filename:
        return jsonify({"error": "Filename not provided"}), 400

    file_path = os.path.join('/in', filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found", "filepath": file_path}), 404

    data = []
    try:
        if filename.endswith('.json'):
            with open(file_path, 'r') as f:
                json_data = json.load(f)
                for item in json_data:
                    data.append((item['id'], item['weight'], item['unit']))
        elif filename.endswith('.csv'):
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                header = next(reader)
                unit = 'kg'
                if len(header) > 1 and 'lbs' in header[1].lower():
                    unit = 'lbs'
                for row in reader:
                    if row:
                        data.append((row[0], row[1], unit))
        else:
            return jsonify({"error": "Invalid file format"}), 400

        conn = get_conn()
        cur = conn.cursor()
        query = "INSERT INTO containers_registered (container_id, weight, unit) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE weight=VALUES(weight), unit=VALUES(unit)"
        cur.executemany(query, data)
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Batch processed", "count": len(data)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
