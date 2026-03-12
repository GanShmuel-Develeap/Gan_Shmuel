from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "weight-app"))

from main import app
from db import get_conn


def test_post_weight_integration():
    conn = get_conn()
    cur = conn.cursor()

    truck_id = "ITEST_TRUCK_20"

    try:
        client = app.test_client()

        resp = client.post(
            "/weight",
            json={
                "direction": "in",
                "truck": truck_id,
                "containers": "ITEST_CONT_20",
                "weight": 1500,
                "unit": "kg",
                "produce": "Apples",
            },
        )
        data = resp.get_json()

        assert resp.status_code == 201
        assert data["status"] == "success"
        assert data["truck"] == truck_id
        assert data["bruto"] == 1500
        assert "id" in data

        cur.execute(
            """
            SELECT direction, truck, containers, bruto, truckTara, neto, produce, unit
            FROM transactions
            WHERE id = %s
            """,
            (data["id"],)
        )
        row = cur.fetchone()

        assert row is not None
        assert row[0] == "in"
        assert row[1] == truck_id
        assert row[2] == "ITEST_CONT_20"
        assert row[3] == 1500
        assert row[4] == 0
        assert row[5] == 0
        assert row[6] == "Apples"
        assert row[7] == "kg"

    finally:
        cur.execute("DELETE FROM transactions WHERE truck = %s", (truck_id,))
        conn.commit()
        cur.close()
        conn.close()