from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "weight-app"))

from main import app
from db import get_conn


def test_get_item_integration():
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO transactions
            (datetime, direction, unit, truck, containers, bruto, truckTara, neto, produce, session_id)
            VALUES
            ('2026-03-10 10:00:00','in','kg','ITEST_TRUCK_2','ITEST_CONT_2',1000,300,700,'Apples',11),
            ('2026-03-10 11:00:00','out','kg','ITEST_TRUCK_2','ITEST_CONT_3',1200,300,900,'Oranges',12)
        """)
        conn.commit()

        client = app.test_client()
        resp = client.get("/item/ITEST_TRUCK_2?from=20260310000000&to=20260310235959")
        data = resp.get_json()

        assert resp.status_code == 200
        assert data["id"] == "ITEST_TRUCK_2"
        assert data["tara"] == 300
        assert data["sessions"] == ["11", "12"]

    finally:
        cur.execute("DELETE FROM transactions WHERE truck = 'ITEST_TRUCK_2'")
        conn.commit()
        cur.close()
        conn.close()