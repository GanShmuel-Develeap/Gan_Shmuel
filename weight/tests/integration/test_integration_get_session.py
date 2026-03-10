from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "weight-app"))

from main import app
from db import get_conn


def test_get_session_integration():
    conn = get_conn()
    cur = conn.cursor()

    try:
        # seed known container tara
        cur.execute("""
            INSERT INTO containers_registered (container_id, weight, unit)
            VALUES ('ITEST_CONT_10', 100, 'kg')
        """)

        # seed one IN and one OUT transaction in same session
        cur.execute("""
            INSERT INTO transactions
            (datetime, direction, truck, containers, bruto, truckTara, neto, produce, unit, session_id)
            VALUES
            ('2026-03-10 10:00:00', 'in',  'ITEST_TRUCK_10', 'ITEST_CONT_10', 1000, 0,   0, 'Apples', 'kg', 'ITEST_SESSION_10'),
            ('2026-03-10 11:00:00', 'out', 'ITEST_TRUCK_10', 'ITEST_CONT_10', 0,    300, 0, 'Apples', 'kg', 'ITEST_SESSION_10')
        """)
        conn.commit()

        client = app.test_client()
        resp = client.get("/session/ITEST_SESSION_10")
        data = resp.get_json()

        assert resp.status_code == 200
        assert data["session_id"] == "ITEST_SESSION_10"
        assert data["truck"] == "ITEST_TRUCK_10"
        assert len(data["transactions"]) == 2
        assert data["neto"] == 600
        assert data["session_summary"]["in_weight"] == 1000
        assert data["session_summary"]["out_weight"] == 300
        assert data["session_summary"]["calculated_neto"] == 600

    finally:
        cur.execute("DELETE FROM transactions WHERE session_id = 'ITEST_SESSION_10'")
        cur.execute("DELETE FROM containers_registered WHERE container_id = 'ITEST_CONT_10'")
        conn.commit()
        cur.close()
        conn.close()