from flask import Blueprint, jsonify
from db import get_conn

test_bp = Blueprint("test", __name__)

@test_bp.route("/transactions/mock", methods=["POST"])
def create_mock_transaction():
    conn = get_conn()
    cur = conn.cursor()

    query = """
        INSERT INTO transactions
        (datetime, direction, truck, containers, bruto, truckTara, neto, produce, session_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        "2026-03-08 10:30:00",
        "IN",
        "TRUCK-123",
        "CONT-001,CONT-002",
        30000,
        12000,
        18000,
        "Apples",
        1
    )

    cur.execute(query, values)
    conn.commit()

    new_id = cur.lastrowid

    cur.close()
    conn.close()

    return jsonify(message="Mock transaction created", id=new_id), 201