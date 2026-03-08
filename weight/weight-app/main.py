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
        SELECT id, direction, bruto, neto, unit, produce, containers
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

    cur.close()
    conn.close()

    return jsonify(rows)
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)