from flask import Blueprint, jsonify
from db import get_conn
from datetime import datetime, timedelta

test_bp = Blueprint("test", __name__)

@test_bp.route("/transactions/mock1", methods=["POST"])
def create_mock_transactions():
    conn = get_conn()
    cur = conn.cursor()

    base = datetime(2026, 3, 8, 8, 0, 0)

    rows = [
    #   (datetime,                  direction, truck,        containers,       bruto,truckTara,neto, produce, session_id)
        (base + timedelta(minutes=10), "out", "TRUCK-1", "CONT-001,CONT-002",  20000, 10000, 7000, "Apples", 1),        
        (base + timedelta(minutes=20), "in",  "TRUCK-1", "CONT-001,CONT-002",  20000, 10000, 7000, "Apples", 1),   
        (base + timedelta(minutes=40), "out", "TRUCK-2", "CONT-003,CONT-004",  30000, 12000, 11000, "Bananas", 2),
        (base + timedelta(minutes=50), "in",  "TRUCK-2", "CONT-003,CONT-004",  30000, 12000, 11000, "Bananas", 2),     
        (base + timedelta(minutes=70), "out", "TRUCK-3", "CONT-005,CONT-006",  30000, 12000, 18000, "Oranges", 3),
        (base + timedelta(minutes=80), "in",  "TRUCK-3", "CONT-005,CONT-006",  30000, 12000, 18000, "Oranges", 3),
    ]

    query = """
        INSERT INTO transactions
        (datetime, direction, truck, containers, bruto, truckTara, neto, produce, session_id)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    for r in rows:
        cur.execute(query, r)

    conn.commit()
    cur.close()
    conn.close()

    return jsonify(message="10 mock transactions inserted"), 201

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
        "in",
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

@test_bp.route("/containers/mock_known", methods=["POST"])
def create_known_mock_containers_known():
    conn = get_conn()
    cur = conn.cursor()

    rows = [
        ("CONT-001", 1000, "kg"),
        ("CONT-002", 2000, "kg"),
        ("CONT-003", 3000, "kg"),
        ("CONT-004", 4000, "kg"),
    ]

    query = """
        INSERT INTO containers_registered (container_id, weight, unit)
        VALUES (%s, %s, %s)
    """

    for r in rows:
        cur.execute(query, r)

    conn.commit()

    cur.close()
    conn.close()

    return jsonify(message="Mock containers inserted", count=len(rows)), 201

@test_bp.route("/containers/mock_unknown", methods=["POST"])
def create_known_mock_containers_unknown():
    conn = get_conn()
    cur = conn.cursor()

    rows = [
        ("CONT-005", None, "kg"),
        ("CONT-006", 1000, "kg"),
    ]

    query = """
        INSERT INTO containers_registered (container_id, weight, unit)
        VALUES (%s, %s, %s)
    """

    for r in rows:
        cur.execute(query, r)

    conn.commit()

    cur.close()
    conn.close()

    return jsonify(message="Mock containers inserted", count=len(rows)), 201
