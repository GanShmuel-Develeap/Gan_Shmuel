import os
import time
import json
import csv
from flask import Flask, jsonify, request
import mysql.connector
from mysql.connector import Error
from test_routes import test_bp
from db import get_conn

app = Flask(__name__)
app.register_blueprint(test_bp)


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
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM transactions")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(rows)

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
