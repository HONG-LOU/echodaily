import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.errors import IntegrationError, ServiceUnavailableError  # noqa: E402
from app.integrations.tencent_oral_evaluation_client import (
    TencentOralEvaluationClient,  # noqa: E402
)


def test_map_sdk_exception_returns_actionable_account_unavailable_error() -> None:
    client = TencentOralEvaluationClient()
    exc = TencentCloudSDKException(
        "AuthFailure.AccountUnavailable",
        "账号未开通口语评测服务或账号已欠费隔离。",
    )

    mapped = client._map_sdk_exception(exc)

    assert isinstance(mapped, ServiceUnavailableError)
    assert mapped.code == "speech_assessment_account_unavailable"
    assert "已开通口语评测服务" in mapped.message


def test_map_sdk_exception_keeps_generic_failures_as_integration_errors() -> None:
    client = TencentOralEvaluationClient()
    exc = TencentCloudSDKException(
        "InternalError",
        "内部错误。",
    )

    mapped = client._map_sdk_exception(exc)

    assert isinstance(mapped, IntegrationError)
    assert mapped.code == "speech_assessment_failed"


def test_build_word_supports_new_websocket_dict_payload() -> None:
    client = TencentOralEvaluationClient()

    word = client._build_word(
        {
            "Word": "concise",
            "MatchTag": 3,
            "PronAccuracy": 61,
            "PronFluency": 0.7,
            "PhoneInfos": [
                {
                    "ReferencePhone": "kən",
                    "Phone": "kən",
                    "Stress": False,
                    "DetectedStress": False,
                },
                {
                    "ReferencePhone": "saɪs",
                    "Phone": "sais",
                    "Stress": True,
                    "DetectedStress": False,
                },
            ],
        }
    )

    assert word.word == "concise"
    assert word.match_tag == 3
    assert word.pronunciation_score == 61
    assert word.fluency_score == 70
    assert word.expected_ipa == "/kən saɪs/"
    assert word.observed_ipa == "/kən sais/"
    assert word.stress_mismatch_count == 1


def test_build_websocket_request_uses_signed_new_api_url() -> None:
    client = TencentOralEvaluationClient()
    client._cached_cloud_app_id = "1315025902"

    voice_id, websocket_url = client._build_websocket_request(
        reference_text="Clear is kind.",
        audio_format="mp3",
    )

    parsed = urlparse(websocket_url)
    query = parse_qs(parsed.query)

    assert parsed.scheme == "wss"
    assert parsed.netloc == "soe.cloud.tencent.com"
    assert parsed.path == "/soe/api/1315025902"
    assert query["voice_id"] == [voice_id]
    assert query["voice_format"] == ["2"]
    assert query["server_engine_type"] == ["16k_en"]
    assert query["signature"]
