import os
import sys
import tempfile
from datetime import date
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

from app.api.dependencies import (  # noqa: E402
    daily_message_client,
    oral_evaluation_client,
    wechat_auth_client,
)
from app.api.routers import dashboard as dashboard_router  # noqa: E402
from app.api.routers import lessons as lessons_router  # noqa: E402
from app.core.errors import ServiceUnavailableError  # noqa: E402
from app.integrations.deepseek_daily_message_client import GeneratedDailyMessage  # noqa: E402
from app.integrations.deepseek_daily_message_client import GeneratedLessonCandidate  # noqa: E402
from app.integrations.tencent_oral_evaluation_client import (  # noqa: E402
    EvaluatedWord,
    OralEvaluationResult,
)
from app.integrations.wechat_auth_client import WechatSessionData  # noqa: E402
from app.main import app  # noqa: E402


def freeze_today(monkeypatch, frozen_day: date) -> None:
    class FrozenDate(date):
        @classmethod
        def today(cls) -> date:
            return frozen_day

    monkeypatch.setattr(dashboard_router, "date", FrozenDate)
    monkeypatch.setattr(lessons_router, "date", FrozenDate)


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


def test_dashboard_endpoint_returns_today_lesson(monkeypatch) -> None:
    freeze_today(monkeypatch, date(2026, 4, 10))
    monkeypatch.setattr(
        daily_message_client,
        "generate_message",
        AsyncMock(
            return_value=GeneratedDailyMessage(
                text="今天先把这一句读顺，状态会慢慢回来。",
                provider="deepseek",
                model="deepseek-chat",
            )
        ),
    )

    with TestClient(app) as client:
        headers = login_and_get_headers(client, openid="openid-dashboard", nickname="Mia")
        response = client.get("/api/v1/dashboard", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["today_lesson"]["id"] == "lesson-bbc-morning"
    assert payload["user"]["nickname"] == "Mia"
    assert payload["daily_message"] == "今天先把这一句读顺，状态会慢慢回来。"
    assert "recent_scores" in payload
    assert "challenge_spotlight" not in payload


def test_dashboard_endpoint_caches_daily_message_for_the_same_day(monkeypatch) -> None:
    freeze_today(monkeypatch, date(2026, 4, 11))
    generate_message = AsyncMock(
        return_value=GeneratedDailyMessage(
            text="先把今天这句读稳，节奏感比着急更重要。",
            provider="deepseek",
            model="deepseek-chat",
        )
    )
    monkeypatch.setattr(daily_message_client, "generate_message", generate_message)

    with TestClient(app) as client:
        headers = login_and_get_headers(client, openid="openid-dashboard-cache", nickname="Noa")
        first_response = client.get("/api/v1/dashboard", headers=headers)
        second_response = client.get("/api/v1/dashboard", headers=headers)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["daily_message"] == "先把今天这句读稳，节奏感比着急更重要。"
    assert second_response.json()["daily_message"] == "先把今天这句读稳，节奏感比着急更重要。"
    assert generate_message.await_count == 1


def test_lessons_endpoint_returns_exact_schedule(monkeypatch) -> None:
    freeze_today(monkeypatch, date(2026, 4, 9))

    with TestClient(app) as client:
        response = client.get("/api/v1/lessons/today")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "lesson-office-kind"


def test_recent_lessons_endpoint_returns_fifty_cards(monkeypatch) -> None:
    freeze_today(monkeypatch, date(2026, 4, 10))
    daily_message_client.generate_lesson_candidates = AsyncMock(
        side_effect=lambda **kwargs: [
            GeneratedLessonCandidate(
                title=f"AI Test {idx + 1}",
                subtitle="AI 句库 · 测试",
                pack_name="AI 每日精选",
                english_text=f"This is generated practice line number {idx + 1}.",
                translation=f"这是第 {idx + 1} 条生成练习句。",
                scenario="测试场景",
                mode_hint="先慢读，再连读。",
                blind_box_prompt="测试盲盒提示",
                tags=["AI句库", "测试"],
                difficulty="Intermediate",
                estimated_seconds=20,
                poster_blurb="测试海报文案",
                theme_tone="mint-latte",
            )
            for idx in range(int(kwargs.get("count", 0)))
        ]
    )

    with TestClient(app) as client:
        response = client.get("/api/v1/lessons/recent")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 50
    assert all("mode_hint" in item for item in payload)


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


def test_assessment_creation_surfaces_service_unavailable_message() -> None:
    oral_evaluation_client.evaluate_sentence = AsyncMock(
        side_effect=ServiceUnavailableError(
            "腾讯云口语评测服务当前不可用，请确认账号已开通口语评测服务且未欠费。",
            code="speech_assessment_account_unavailable",
        )
    )
    payload = {
        "lesson_id": "lesson-office-kind",
        "duration_seconds": 22,
        "audio_format": "mp3",
        "audio_base64": "YXVkaW8=",
    }

    with TestClient(app) as client:
        headers = login_and_get_headers(client, openid="openid-assessment-error", nickname="Luna")
        response = client.post("/api/v1/assessments", json=payload, headers=headers)

    assert response.status_code == 503
    error_payload = response.json()
    assert error_payload["code"] == "speech_assessment_account_unavailable"
    assert "未欠费" in error_payload["message"]


def test_assessment_creation_limited_to_ten_times_per_day() -> None:
    oral_evaluation_client.evaluate_sentence = AsyncMock(
        return_value=OralEvaluationResult(
            session_id="session-limit",
            request_id="request-limit",
            overall_score=80,
            pronunciation_score=80,
            fluency_score=80,
            completeness_score=80,
            stress_score=80,
            recognized_text="Test sentence.",
            words=[],
        )
    )
    payload = {
        "lesson_id": "lesson-office-kind",
        "duration_seconds": 20,
        "audio_format": "mp3",
        "audio_base64": "YXVkaW8=",
    }

    with TestClient(app) as client:
        headers = login_and_get_headers(client, openid="openid-assessment-limit", nickname="Mia")
        for _ in range(10):
            response = client.post("/api/v1/assessments", json=payload, headers=headers)
            assert response.status_code == 201

        exceeded_response = client.post("/api/v1/assessments", json=payload, headers=headers)

    assert exceeded_response.status_code == 400
    error_payload = exceeded_response.json()
    assert error_payload["code"] == "daily_assessment_limit_reached"
