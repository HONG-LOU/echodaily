import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

test_database = Path.cwd() / "data" / "test-echodaily.db"
test_database.parent.mkdir(parents=True, exist_ok=True)
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{test_database.as_posix()}"

from app.main import app  # noqa: E402


def test_dashboard_endpoint_returns_today_lesson() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/dashboard", params={"user_id": "demo-user"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["today_lesson"]["id"] == "lesson-office-kind"
    assert payload["user"]["nickname"] == "Mia"


def test_assessment_creation_returns_report() -> None:
    payload = {
        "user_id": "demo-user",
        "lesson_id": "lesson-office-kind",
        "mode": "follow",
        "duration_seconds": 22,
        "transcript": "Clear is kind and concise words travel further in every meeting.",
    }

    with TestClient(app) as client:
        response = client.post("/api/v1/assessments", json=payload)

    assert response.status_code == 201
    report = response.json()
    assert report["overall_score"] >= 70
    assert report["highlights"]
