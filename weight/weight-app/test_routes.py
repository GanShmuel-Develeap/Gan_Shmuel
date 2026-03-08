from flask import Blueprint, jsonify
from db import get_conn
from datetime import datetime, timedelta

test_bp = Blueprint("test", __name__)

@test_bp.route("/transactions/mock10", methods=["POST"])
def create_mock_transactions():
    conn = get_conn()
    cur = conn.cursor()

    base = datetime(2026, 3, 8, 8, 0, 0)

    rows = [
        (base + timedelta(minutes=5),  "in",  "TRUCK-1", "CONT-001",           20000, 10000, 10000, "Apples", 1),
        (base + timedelta(minutes=10), "out", "TRUCK-2", "CONT-002",           21000, 11000, 10000, "Oranges", 1),
        (base + timedelta(minutes=15), "in",  "TRUCK-3", "CONT-003,CONT-004",  30000, 12000, 18000, "Bananas", 1),
        (base + timedelta(minutes=20), "out", "TRUCK-4", "CONT-005",           22000, 11000, 11000, "Apples", 1),
        (base + timedelta(minutes=25), "none","TRUCK-5", "CONT-006",           18000,  9000,  9000, "Pears", 1),
        (base + timedelta(minutes=30), "in",  "TRUCK-6", "CONT-007",           25000, 12000, 13000, "Apples", 1),
        (base + timedelta(minutes=35), "out", "TRUCK-7", "CONT-008",           24000, 11000, 13000, "Oranges", 1),
        (base + timedelta(minutes=40), "in",  "TRUCK-8", "CONT-009",           26000, 12000, 14000, "Bananas", 1),
        (base + timedelta(minutes=45), "none","TRUCK-9", "CONT-010",           17000,  8000,  9000, "Pears", 1),
        (base + timedelta(minutes=50), "out", "TRUCK-10","CONT-011,CONT-012",  31000, 13000, 18000, "Apples", 1),
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
        ("CONT-002", 1200, "kg"),
        ("CONT-003", 900, "kg"),
        ("CONT-004", 1100, "kg"),
        ("CONT-005", 5000, "kg"),
        ("CONT-006", 950, "kg"),
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
        ("CONT-007", None, "kg"),
        ("CONT-008", None, "kg"),
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
