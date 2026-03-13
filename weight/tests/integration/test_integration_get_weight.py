from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "weight-app"))

from main import app
from db import get_conn


def test_get_all_transactions_integration():
    conn = get_conn()
    cur = conn.cursor()

    try:
        # insert only test rows
        cur.execute("""
            INSERT INTO containers_registered (container_id, weight, unit)
            VALUES ('ITEST_CONT_1', 100, 'kg')
        """)

        cur.execute("""
            INSERT INTO transactions
            (datetime, direction, unit, truck, containers, bruto, truckTara, neto, produce, session_id)
            VALUES ('2026-03-10 10:00:00','in','kg','ITEST_TRUCK_1','ITEST_CONT_1',1000,200,800,'Apples',1)
        """)

        conn.commit()

        client = app.test_client()
        resp = client.get("/weight?from=20260310000000&to=20260310235959")
        data = resp.get_json()

        row = next(r for r in data if r["truck_id"] == "ITEST_TRUCK_1")

        assert resp.status_code == 200
        assert row["neto"] == 800
        assert row["containers"] == ["ITEST_CONT_1"]

    finally:
        # cleanup only test data
        cur.execute("DELETE FROM transactions WHERE truck='ITEST_TRUCK_1'")
        cur.execute("DELETE FROM containers_registered WHERE container_id='ITEST_CONT_1'")
        conn.commit()
        cur.close()
        conn.close()