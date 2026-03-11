from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "weight-app"))

from main import app
from db import get_conn


def test_get_unknown_integration():
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO containers_registered (container_id, weight, unit)
            VALUES
            ('ITEST_UNKNOWN_1', NULL, 'kg'),
            ('ITEST_KNOWN_1', 100, 'kg')
        """)
        conn.commit()

        client = app.test_client()
        resp = client.get("/unknown")
        data = resp.get_json()

        assert resp.status_code == 200
        assert "ITEST_UNKNOWN_1" in data
        assert "ITEST_KNOWN_1" not in data

    finally:
        cur.execute("""
            DELETE FROM containers_registered
            WHERE container_id IN ('ITEST_UNKNOWN_1', 'ITEST_KNOWN_1')
        """)
        conn.commit()
        cur.close()
        conn.close()