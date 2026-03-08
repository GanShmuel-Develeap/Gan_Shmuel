import os
import time
from flask import Flask, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "db"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "database": os.getenv("DB_NAME", "appdb"),
    "user": os.getenv("DB_USER", "appuser"),
    "password": os.getenv("DB_PASSWORD", "apppass"),
}

def get_conn(retries=30, delay=1):
    last_err = None
    for _ in range(retries):
        try:
            return mysql.connector.connect(**DB_CONFIG)
        except Error as e:
            last_err = e
            time.sleep(delay)
    raise last_err

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

@app.route('/transactions/mock', methods=['POST'])
def create_mock_transaction():
    conn = get_conn()
    cur = conn.cursor()

    query = """
        INSERT INTO transactions
        (datetime, direction, truck, containers, bruto, truckTara, neto, produce)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        "2026-03-08 10:30:00",
        "IN",
        "TRUCK-123",
        "CONT-001,CONT-002",
        30000,
        12000,
        18000,
        "Apples"
    )

    cur.execute(query, values)
    conn.commit()

    new_id = cur.lastrowid

    cur.close()
    conn.close()

    return jsonify(message="Mock transaction created", id=new_id), 201


@app.route('/transactions', methods=['GET'])
def get_all_transactions():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM transactions")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(rows)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)