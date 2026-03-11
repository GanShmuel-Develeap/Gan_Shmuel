from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "weight-app"))

from main import app
from db import get_conn


def test_weight_submit_integration():
    conn = get_conn()
    cur = conn.cursor()

    try:
        client = app.test_client()

        resp = client.post(
            "/weight-form",
            data={
                "direction": "in",
                "truck": "ITEST_TRUCK_20",
                "containers": "ITEST_CONT_20",
                "bruto": "1500",
                "unit": "kg",
                "produce": "Apples",
            },
        )
        data = resp.get_json()

        assert resp.status_code == 201
        assert data["status"] == "success"
        assert data["truck"] == "ITEST_TRUCK_20"
        assert data["bruto"] == 1500
        assert "id" in data

        cur.execute("""
            SELECT direction, truck, containers, bruto, truckTara, neto, produce, unit
            FROM transactions
            WHERE id = %s
        """, (data["id"],))
        row = cur.fetchone()

        assert row is not None
        assert row[0] == "in"
        assert row[1] == "ITEST_TRUCK_20"
        assert row[2] == "ITEST_CONT_20"
        assert row[3] == 1500
        assert row[4] == 0
        assert row[5] == 0
        assert row[6] == "Apples"
        assert row[7] == "kg"

    finally:
        cur.execute("DELETE FROM transactions WHERE truck = 'ITEST_TRUCK_20'")
        conn.commit()
        cur.close()
        conn.close()