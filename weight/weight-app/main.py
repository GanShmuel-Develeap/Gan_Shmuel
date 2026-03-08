import os
import time
from flask import Flask, jsonify, request
from datetime import datetime
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


@app.route('/weight_basic', methods=['GET'])
def get_all_transactions_basic():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM transactions")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(rows)

from datetime import datetime
from flask import request, jsonify

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
        SELECT id, direction, bruto, neto, produce, containers
        FROM transactions
        WHERE datetime BETWEEN %s AND %s
        AND direction IN ({placeholders})
        ORDER BY id
        """,
        [t1, t2] + directions
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([
        {
            "id": row["id"],
            "direction": row["direction"],
            "bruto": row["bruto"],
            "neto": row["neto"] if row["neto"] is not None else "na",
            "produce": row["produce"],
            "containers": row["containers"].split(",") if row["containers"] else []
        }
        for row in rows
    ])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)