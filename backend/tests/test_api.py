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
os.environ["TENCENTCLOUD_SECRET_ID"] = "test-secret-id"
os.environ["TENCENTCLOUD_SECRET_KEY"] = "test-secret-key"

from app.api.dependencies import oral_evaluation_client, wechat_auth_client  # noqa: E402
from app.integrations.tencent_oral_evaluation_client import (  # noqa: E402
    EvaluatedWord,
    OralEvaluationResult,
)
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
    assert "recent_scores" in payload
    assert "challenge_spotlight" not in payload


def test_assessment_creation_returns_report() -> None:
    oral_evaluation_client.evaluate_sentence = AsyncMock(
        return_value=OralEvaluationResult(
            session_id="session-1",
            request_id="request-1",
            overall_score=86,
            pronunciation_score=88,
            fluency_score=84,
            completeness_score=92,
            stress_score=79,
            recognized_text="Clear is kind and concise words travel further in every meeting.",
            words=[
                EvaluatedWord(
                    word="concise",
                    match_tag=3,
                    pronunciation_score=61,
                    fluency_score=70,
                    expected_ipa="/kən ˈsaɪs/",
                    observed_ipa="/kən ˈsais/",
                    stress_mismatch_count=1,
                ),
                EvaluatedWord(
                    word="meeting",
                    match_tag=0,
                    pronunciation_score=94,
                    fluency_score=90,
                    expected_ipa="/ˈmiː tɪŋ/",
                    observed_ipa="/ˈmiː tɪŋ/",
                    stress_mismatch_count=0,
                ),
            ],
        )
    )
    payload = {
        "lesson_id": "lesson-office-kind",
        "duration_seconds": 22,
        "audio_format": "mp3",
        "audio_base64": "YXVkaW8=",
    }

    with TestClient(app) as client:
        headers = login_and_get_headers(client, openid="openid-assessment", nickname="Luna")
        response = client.post("/api/v1/assessments", json=payload, headers=headers)

    assert response.status_code == 201
    report = response.json()
    assert report["overall_score"] == 86
    assert report["recognized_text"].startswith("Clear is kind")
    assert report["highlights"]
