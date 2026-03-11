from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "weight-app"))

from main import app
from db import get_conn


def test_batch_weight_integration():
    tmp_file = Path("/in/itest_batch_weight.json")

    conn = get_conn()
    cur = conn.cursor()

    try:
        # create temporary input file
        tmp_file.write_text(json.dumps([
            {"id": "ITEST_CONT_30", "weight": 100, "unit": "kg"}
        ]))

        client = app.test_client()
        resp = client.post("/batch-weight", data={"file": tmp_file.name})
        data = resp.get_json()

        assert resp.status_code == 200
        assert data["message"] == "Batch processed"
        assert data["count"] == 1

        # verify DB insert
        cur.execute("""
            SELECT container_id, weight, unit
            FROM containers_registered
            WHERE container_id = 'ITEST_CONT_30'
        """)
        row = cur.fetchone()

        assert row is not None
        assert row[0] == "ITEST_CONT_30"
        assert row[1] == 100
        assert row[2] == "kg"

    finally:
        # cleanup DB
        cur.execute("DELETE FROM containers_registered WHERE container_id = 'ITEST_CONT_30'")
        conn.commit()
        cur.close()
        conn.close()

        # cleanup file
        if tmp_file.exists():
            tmp_file.unlink()