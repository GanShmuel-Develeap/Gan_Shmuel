import os
import time
from flask import Flask, jsonify, render_template, request
import mysql.connector
from mysql.connector import Error
from weight_service import submit_weight_transaction, get_session_info
from db import get_conn
from test_routes import test_bp

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)