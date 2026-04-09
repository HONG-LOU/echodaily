import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

test_database = Path(tempfile.gettempdir()) / f"echodaily-test-{uuid4().hex}.db"
test_database.parent.mkdir(parents=True, exist_ok=True)
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{test_database.as_posix()}"
os.environ["WECHAT_APP_ID"] = "wx-test-appid"
os.environ["WECHAT_APP_SECRET"] = "wx-test-secret"

from app.api.dependencies import wechat_auth_client  # noqa: E402
from app.integrations.wechat_auth_client import WechatSessionData  # noqa: E402
from app.main import app  # noqa: E402


def login_and_get_headers(
    client: TestClient,
    *,
    openid: str,
    nickname: str,
) -> dict[str, str]:
    wechat_auth_client.exchange_code = AsyncMock(
        return_value=WechatSessionData(openid=openid, unionid=None)
    )

    response = client.post(
        "/api/v1/auth/wechat/login",
        json={
            "code": f"code-{openid}",
            "nickname": nickname,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    return {"Authorization": f"Bearer {payload['access_token']}"}


def test_dashboard_requires_login() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/dashboard")

    assert response.status_code == 401
    assert response.json()["code"] == "missing_access_token"


def test_dashboard_endpoint_returns_today_lesson() -> None:
    with TestClient(app) as client:
        headers = login_and_get_headers(client, openid="openid-dashboard", nickname="Mia")
        response = client.get("/api/v1/dashboard", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["today_lesson"]["id"] == "lesson-office-kind"
    assert payload["user"]["nickname"] == "Mia"


def test_assessment_creation_returns_report() -> None:
    payload = {
        "lesson_id": "lesson-office-kind",
        "mode": "follow",
        "duration_seconds": 22,
        "transcript": "Clear is kind and concise words travel further in every meeting.",
    }

    with TestClient(app) as client:
        headers = login_and_get_headers(client, openid="openid-assessment", nickname="Luna")
        response = client.post("/api/v1/assessments", json=payload, headers=headers)

    assert response.status_code == 201
    report = response.json()
    assert report["overall_score"] >= 70
    assert report["highlights"]
