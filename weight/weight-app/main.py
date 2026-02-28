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
def hello():
    return "Flask + MySQL (docker-compose) ✅\n"

@app.get("/db")
def db_check():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT NOW()")
    (now,) = cur.fetchone()

    cur.close()
    conn.close()

    return jsonify(mysql_time=str(now))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)