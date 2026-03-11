from pathlib import Path
import sys
import time

# allow importing the app
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "weight-app"))

from main import app
from db import get_conn


def cleanup_all():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM transactions")
    cur.execute("DELETE FROM transaction_events")
    conn.commit()
    cur.close()
    conn.close()


def test_abandoned_sessions_endpoint():
    # ensure a clean slate
    cleanup_all()
    client = app.test_client()

    # create an IN transaction
    payload = {
        "direction": "in",
        "truck": "ABANDON-TRUCK",
        "containers": "C-X",
        "weight": 1234,
        "unit": "kg"
    }
    resp = client.post("/weight", json=payload)
    assert resp.status_code == 201
    data = resp.get_json()
    session_id = data.get("session_id", None)
    assert session_id

    # call abandoned endpoint with zero timeout to return immediately
    resp2 = client.get('/sessions/abandoned?timeout=0')
    assert resp2.status_code == 200
    abandoned = resp2.get_json()
    assert any(s['session_id'] == session_id for s in abandoned)

    cleanup_all()


def test_session_audit_endpoint():
    # clean
    cleanup_all()
    client = app.test_client()

    # create IN transaction and then OUT so events exist
    payload_in = {
        "direction": "in",
        "truck": "AUDIT-TRUCK",
        "containers": "C-A",
        "weight": 2000,
        "unit": "kg"
    }
    resp_in = client.post("/weight", json=payload_in)
    assert resp_in.status_code == 201
    session_id = resp_in.get_json().get('session_id')
    assert session_id

    # add OUT
    payload_out = {
        "direction": "out",
        "truck": "AUDIT-TRUCK",
        "weight": 1900,
        "unit": "kg"
    }
    resp_out = client.post("/weight", json=payload_out)
    assert resp_out.status_code == 201

    # now query audit
    resp_audit = client.get(f"/sessions/{session_id}/audit")
    assert resp_audit.status_code == 200
    events = resp_audit.get_json()
    # at least two events (insert in, insert out)
    assert len(events) >= 2

    cleanup_all()
