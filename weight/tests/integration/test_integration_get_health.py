from pathlib import Path
import sys

# allow importing the app
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "weight-app"))

from main import app


def test_health_endpoint():
    client = app.test_client()

    resp = client.get("/health")
    data = resp.get_json()

    assert resp.status_code == 200
    assert "mysql_time" in data
