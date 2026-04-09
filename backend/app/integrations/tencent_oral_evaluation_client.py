from __future__ import annotations

import asyncio
import base64
import binascii
import hashlib
import hmac
import json
import logging
import random
import re
import time
import urllib.parse
from dataclasses import dataclass
from typing import Any, Literal
from uuid import uuid4

from tencentcloud.common import credential
from tencentcloud.common.common_client import CommonClient
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.soe.v20180724 import models, soe_client
from websockets.asyncio.client import connect as websocket_connect
from websockets.exceptions import WebSocketException

from app.core.config import get_settings
from app.core.errors import AppError, BadRequestError, IntegrationError, ServiceUnavailableError

type AudioFormat = Literal["mp3", "wav", "pcm", "speex"]

LEGACY_VOICE_FILE_TYPE_MAP: dict[AudioFormat, int] = {
    "pcm": 1,
    "wav": 2,
    "mp3": 3,
    "speex": 4,
}
NEW_VOICE_FORMAT_MAP: dict[AudioFormat, int] = {
    "pcm": 0,
    "wav": 1,
    "mp3": 2,
    "speex": 4,
}

MATCH_TAG_MATCHED = 0
MATCH_TAG_INSERTED = 1
MATCH_TAG_MISSING = 2
MATCH_TAG_MISREAD = 3
MATCH_TAG_UNRECORDED = 4

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class EvaluatedWord:
    word: str
    match_tag: int
    pronunciation_score: int
    fluency_score: int
    expected_ipa: str
    observed_ipa: str
    stress_mismatch_count: int


@dataclass(slots=True)
class OralEvaluationResult:
    session_id: str
    request_id: str
    overall_score: int
    pronunciation_score: int
    fluency_score: int
    completeness_score: int
    stress_score: int
    recognized_text: str
    words: list[EvaluatedWord]


class TencentOralEvaluationClient:
    def __init__(self) -> None:
        self._cached_cloud_app_id: str | None = None

    async def evaluate_sentence(
        self,
        *,
        reference_text: str,
        audio_base64: str,
        audio_format: AudioFormat,
    ) -> OralEvaluationResult:
        settings = get_settings()
        if settings.tencentcloud_soe_transport == "legacy_sdk":
            return await asyncio.to_thread(
                self._evaluate_sentence_sync,
                reference_text,
                audio_base64,
                audio_format,
            )
        return await self._evaluate_sentence_via_websocket(
            reference_text=reference_text,
            audio_base64=audio_base64,
            audio_format=audio_format,
        )

    def _evaluate_sentence_sync(
        self,
        reference_text: str,
        audio_base64: str,
        audio_format: AudioFormat,
    ) -> OralEvaluationResult:
        settings = get_settings()
        if settings.tencentcloud_secret_id is None or settings.tencentcloud_secret_key is None:
            raise ServiceUnavailableError(
                "腾讯云口语评测尚未配置，请先设置 TENCENTCLOUD_SECRET_ID 和 "
                "TENCENTCLOUD_SECRET_KEY。",
                code="speech_assessment_not_configured",
            )

        if audio_format not in LEGACY_VOICE_FILE_TYPE_MAP:
            raise BadRequestError("暂不支持该音频格式。", code="unsupported_audio_format")

        self._decode_base64_payload(audio_base64)

        session_id = f"assessment-{uuid4().hex}"
        request = models.TransmitOralProcessWithInitRequest()
        request.SeqId = 1
        request.IsEnd = 1
        request.VoiceFileType = LEGACY_VOICE_FILE_TYPE_MAP[audio_format]
        request.VoiceEncodeType = 1
        request.UserVoiceData = audio_base64
        request.SessionId = session_id
        request.RefText = reference_text
        request.WorkMode = 1
        request.EvalMode = 1
        request.ScoreCoeff = settings.tencentcloud_soe_score_coeff
        request.SentenceInfoEnabled = 0
        request.ServerType = 0
        request.IsAsync = 0
        request.IsQuery = 0
        request.TextMode = 0
        if settings.tencentcloud_soe_app_id is not None:
            request.SoeAppId = settings.tencentcloud_soe_app_id

        try:
            response = self._build_client().TransmitOralProcessWithInit(request)
        except TencentCloudSDKException as exc:
            raise self._map_sdk_exception(exc) from exc

        if response.Status == "Failed":
            raise IntegrationError(
                "腾讯云口语评测未能完成，请重新录音后再试。",
                code="speech_assessment_failed",
            )

        words = [self._build_word(item) for item in response.Words or []]
        pronunciation_score = self._normalize_percentage(response.PronAccuracy)
        fluency_score = self._normalize_unit_score(response.PronFluency)
        completeness_score = self._normalize_unit_score(response.PronCompletion)
        overall_score = self._normalize_percentage(response.SuggestedScore)
        stress_score = self._calculate_stress_score(words, fallback=pronunciation_score)

        return OralEvaluationResult(
            session_id=response.SessionId or session_id,
            request_id=response.RequestId or "",
            overall_score=overall_score,
            pronunciation_score=pronunciation_score,
            fluency_score=fluency_score,
            completeness_score=completeness_score,
            stress_score=stress_score,
            recognized_text=self._build_recognized_text(words),
            words=words,
        )

    async def _evaluate_sentence_via_websocket(
        self,
        *,
        reference_text: str,
        audio_base64: str,
        audio_format: AudioFormat,
    ) -> OralEvaluationResult:
        settings = get_settings()
        if settings.tencentcloud_secret_id is None or settings.tencentcloud_secret_key is None:
            raise ServiceUnavailableError(
                "腾讯云口语评测尚未配置，请先设置 TENCENTCLOUD_SECRET_ID 和 "
                "TENCENTCLOUD_SECRET_KEY。",
                code="speech_assessment_not_configured",
            )
        if audio_format not in NEW_VOICE_FORMAT_MAP:
            raise BadRequestError("暂不支持该音频格式。", code="unsupported_audio_format")

        audio_bytes = self._decode_base64_payload(audio_base64)
        voice_id, websocket_url = self._build_websocket_request(
            reference_text=reference_text,
            audio_format=audio_format,
        )
        timeout_seconds = settings.tencentcloud_soe_req_timeout_seconds

        try:
            async with asyncio.timeout(timeout_seconds):
                async with websocket_connect(
                    websocket_url,
                    max_size=8 * 1024 * 1024,
                    open_timeout=timeout_seconds,
                ) as websocket:
                    handshake_payload = self._parse_websocket_message(await websocket.recv())
                    self._raise_new_api_error_if_needed(handshake_payload)

                    await websocket.send(audio_bytes)
                    await websocket.send(json.dumps({"type": "end"}))

                    final_payload: dict[str, Any] | None = None
                    while True:
                        message_payload = self._parse_websocket_message(await websocket.recv())
                        self._raise_new_api_error_if_needed(message_payload)
                        if int(message_payload.get("final", 0) or 0) == 1:
                            final_payload = message_payload
                            break

                    if final_payload is None:
                        raise IntegrationError(
                            "腾讯云口语评测未返回最终结果，请稍后重试。",
                            code="speech_assessment_failed",
                        )
        except asyncio.TimeoutError as exc:
            raise IntegrationError(
                "腾讯云口语评测超时，请稍后重试。",
                code="speech_assessment_timeout",
            ) from exc
        except WebSocketException as exc:
            logger.warning("Tencent oral evaluation websocket failed: %s", exc)
            raise IntegrationError(
                "腾讯云口语评测连接失败，请稍后重试。",
                code="speech_assessment_failed",
            ) from exc
        except OSError as exc:
            logger.warning("Tencent oral evaluation network failure: %s", exc)
            raise IntegrationError(
                "腾讯云口语评测网络异常，请稍后重试。",
                code="speech_assessment_failed",
            ) from exc

        result = final_payload.get("result") or {}
        words = [self._build_word(item) for item in result.get("Words") or []]
        pronunciation_score = self._normalize_percentage(result.get("PronAccuracy"))
        fluency_score = self._normalize_unit_score(result.get("PronFluency"))
        completeness_score = self._normalize_unit_score(result.get("PronCompletion"))
        overall_score = self._normalize_percentage(result.get("SuggestedScore"))
        stress_score = self._calculate_stress_score(words, fallback=pronunciation_score)

        return OralEvaluationResult(
            session_id=voice_id,
            request_id=voice_id,
            overall_score=overall_score,
            pronunciation_score=pronunciation_score,
            fluency_score=fluency_score,
            completeness_score=completeness_score,
            stress_score=stress_score,
            recognized_text=self._build_recognized_text(words),
            words=words,
        )

    def _build_client(self) -> soe_client.SoeClient:
        settings = get_settings()
        http_profile = HttpProfile(
            endpoint="soe.tencentcloudapi.com",
            reqTimeout=settings.tencentcloud_soe_req_timeout_seconds,
        )
        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile
        cred = credential.Credential(
            settings.tencentcloud_secret_id,
            settings.tencentcloud_secret_key,
        )
        return soe_client.SoeClient(
            cred,
            settings.tencentcloud_soe_region or "ap-guangzhou",
            client_profile,
        )

    def _decode_base64_payload(self, audio_base64: str) -> bytes:
        if not audio_base64.strip():
            raise BadRequestError("录音内容不能为空。", code="empty_audio_payload")

        try:
            return base64.b64decode(audio_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise BadRequestError("录音数据不是有效的 Base64 内容。", code="invalid_audio") from exc

    def _build_websocket_request(
        self,
        *,
        reference_text: str,
        audio_format: AudioFormat,
    ) -> tuple[str, str]:
        settings = get_settings()
        secret_id = settings.tencentcloud_secret_id
        secret_key = settings.tencentcloud_secret_key
        if secret_id is None or secret_key is None:
            raise ServiceUnavailableError(
                "腾讯云口语评测尚未配置，请先设置 TENCENTCLOUD_SECRET_ID 和 "
                "TENCENTCLOUD_SECRET_KEY。",
                code="speech_assessment_not_configured",
            )

        app_id = self._resolve_cloud_app_id()
        voice_id = str(uuid4())
        timestamp = int(time.time())
        params: dict[str, str | int | float] = {
            "eval_mode": 1,
            "expired": timestamp + max(60, settings.tencentcloud_soe_req_timeout_seconds * 2),
            "nonce": random.randint(10_000_000, 99_999_999),
            "rec_mode": 1,
            "ref_text": reference_text,
            "score_coeff": settings.tencentcloud_soe_score_coeff,
            "secretid": secret_id,
            "sentence_info_enabled": 0,
            "server_engine_type": settings.tencentcloud_soe_server_engine_type,
            "text_mode": 0,
            "timestamp": timestamp,
            "voice_format": NEW_VOICE_FORMAT_MAP[audio_format],
            "voice_id": voice_id,
        }
        canonical_query = "&".join(f"{key}={params[key]}" for key in sorted(params))
        signature_source = f"soe.cloud.tencent.com/soe/api/{app_id}?{canonical_query}"
        signature = base64.b64encode(
            hmac.new(
                secret_key.encode("utf-8"),
                signature_source.encode("utf-8"),
                hashlib.sha1,
            ).digest()
        ).decode("utf-8")
        signed_query = urllib.parse.urlencode({**params, "signature": signature})
        websocket_url = f"wss://soe.cloud.tencent.com/soe/api/{app_id}?{signed_query}"
        return voice_id, websocket_url

    def _resolve_cloud_app_id(self) -> str:
        settings = get_settings()
        if settings.tencentcloud_app_id is not None:
            return settings.tencentcloud_app_id
        if self._cached_cloud_app_id is not None:
            return self._cached_cloud_app_id

        secret_id = settings.tencentcloud_secret_id
        secret_key = settings.tencentcloud_secret_key
        if secret_id is None or secret_key is None:
            raise ServiceUnavailableError(
                "腾讯云口语评测尚未配置，请先设置 TENCENTCLOUD_SECRET_ID 和 "
                "TENCENTCLOUD_SECRET_KEY。",
                code="speech_assessment_not_configured",
            )

        cred = credential.Credential(secret_id, secret_key)
        client = CommonClient("cam", "2019-01-16", cred, settings.tencentcloud_soe_region)
        try:
            response = client.call_json("GetUserAppId", {})
        except TencentCloudSDKException as exc:
            raise self._map_sdk_exception(exc) from exc

        app_id = str(response.get("Response", {}).get("AppId") or "").strip()
        if not app_id:
            raise ServiceUnavailableError(
                "腾讯云账号缺少可用的 AppId，请检查账号状态或显式配置 TENCENTCLOUD_APP_ID。",
                code="speech_assessment_missing_app_id",
            )
        self._cached_cloud_app_id = app_id
        return app_id

    def _parse_websocket_message(self, raw_message: Any) -> dict[str, Any]:
        if isinstance(raw_message, bytes):
            text = raw_message.decode("utf-8")
        else:
            text = str(raw_message)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            logger.warning("Tencent oral evaluation returned non-JSON payload: %s", text)
            raise IntegrationError(
                "腾讯云口语评测返回了无法解析的数据，请稍后重试。",
                code="speech_assessment_failed",
            ) from exc

    def _raise_new_api_error_if_needed(self, payload: dict[str, Any]) -> None:
        code = int(payload.get("code", 0) or 0)
        if code == 0:
            return

        message = str(payload.get("message") or "腾讯云口语评测调用失败。")
        logger.warning(
            "Tencent oral evaluation websocket request failed",
            extra={
                "tencent_error_code": code,
                "tencent_error_message": message,
                "tencent_voice_id": payload.get("voice_id"),
            },
        )
        if "signature" in message.lower() or "secretid" in message.lower():
            raise ServiceUnavailableError(
                f"腾讯云口语评测鉴权失败：{message}",
                code="speech_assessment_invalid_credentials",
            )
        if "appid" in message.lower():
            raise ServiceUnavailableError(
                f"腾讯云口语评测 AppId 配置无效：{message}",
                code="speech_assessment_missing_app_id",
            )
        raise IntegrationError(
            f"腾讯云口语评测调用失败：{message}",
            code="speech_assessment_failed",
        )

    def _get_field_value(self, item: Any, field_name: str, default: Any = None) -> Any:
        if isinstance(item, dict):
            return item.get(field_name, default)
        return getattr(item, field_name, default)

    def _build_word(self, item: models.WordRsp) -> EvaluatedWord:
        phone_infos = self._get_field_value(item, "PhoneInfos", []) or []
        expected_phones = [
            self._get_field_value(phone, "ReferencePhone") or self._get_field_value(phone, "Phone")
            for phone in phone_infos
            if (
                self._get_field_value(phone, "ReferencePhone")
                or self._get_field_value(phone, "Phone")
            )
        ]
        observed_phones = [
            self._get_field_value(phone, "Phone") or self._get_field_value(phone, "ReferencePhone")
            for phone in phone_infos
            if (
                self._get_field_value(phone, "Phone")
                or self._get_field_value(phone, "ReferencePhone")
            )
        ]
        stress_mismatch_count = sum(
            1
            for phone in phone_infos
            if self._get_field_value(phone, "Stress") is not None
            and self._get_field_value(phone, "DetectedStress") is not None
            and bool(self._get_field_value(phone, "Stress"))
            != bool(self._get_field_value(phone, "DetectedStress"))
        )

        return EvaluatedWord(
            word=str(self._get_field_value(item, "Word", "") or "").strip(),
            match_tag=int(self._get_field_value(item, "MatchTag", 0) or 0),
            pronunciation_score=self._normalize_percentage(self._get_field_value(item, "PronAccuracy")),
            fluency_score=self._normalize_unit_score(self._get_field_value(item, "PronFluency")),
            expected_ipa=self._format_ipa(expected_phones),
            observed_ipa=self._format_ipa(observed_phones),
            stress_mismatch_count=stress_mismatch_count,
        )

    def _build_recognized_text(self, words: list[EvaluatedWord]) -> str:
        recognized_words = [
            item.word
            for item in words
            if item.word and item.match_tag != MATCH_TAG_MISSING
        ]
        raw_text = " ".join(recognized_words).strip()
        if not raw_text:
            return ""
        compact_text = re.sub(r"\s+([,.!?;:])", r"\1", raw_text)
        return re.sub(r"\s+'", "'", compact_text)

    def _calculate_stress_score(self, words: list[EvaluatedWord], *, fallback: int) -> int:
        stress_related_words = [item for item in words if item.expected_ipa]
        if not stress_related_words:
            return fallback

        weighted_total = 0
        weight_sum = 0
        for item in stress_related_words:
            weight = 1 + item.stress_mismatch_count
            item_score = max(0, item.pronunciation_score - item.stress_mismatch_count * 18)
            weighted_total += item_score * weight
            weight_sum += weight

        if weight_sum == 0:
            return fallback
        return round(weighted_total / weight_sum)

    def _normalize_percentage(self, value: float | int | None) -> int:
        if value is None:
            return 0
        return max(0, min(100, round(float(value))))

    def _normalize_unit_score(self, value: float | int | None) -> int:
        if value is None or float(value) < 0:
            return 0
        return max(0, min(100, round(float(value) * 100)))

    def _format_ipa(self, phones: list[str]) -> str:
        compact_phones = [phone.strip() for phone in phones if phone and phone.strip()]
        if not compact_phones:
            return ""
        return f"/{' '.join(compact_phones)}/"

    def _map_sdk_exception(self, exc: TencentCloudSDKException) -> AppError:
        error_code = exc.get_code() or ""
        logger.warning(
            "Tencent oral evaluation request failed",
            extra={
                "tencent_error_code": error_code,
                "tencent_error_message": exc.get_message() or str(exc),
                "tencent_request_id": exc.get_request_id(),
            },
        )
        if error_code in {
            "InvalidCredential",
            "AuthFailure.SecretIdNotFound",
            "AuthFailure.SignatureFailure",
        }:
            return ServiceUnavailableError(
                "腾讯云评测凭证无效，请检查 SecretId / SecretKey 配置。",
                code="speech_assessment_invalid_credentials",
            )
        if error_code == "AuthFailure.AccountUnavailable":
            return ServiceUnavailableError(
                "腾讯云口语评测服务当前不可用，请确认账号已开通口语评测服务且未欠费。",
                code="speech_assessment_account_unavailable",
            )
        if error_code == "RequestLimitExceeded":
            return IntegrationError(
                "腾讯云评测请求过于频繁，请稍后再试。",
                code="speech_assessment_rate_limited",
            )
        return IntegrationError(
            "腾讯云口语评测调用失败，请稍后重试。",
            code="speech_assessment_failed",
        )
