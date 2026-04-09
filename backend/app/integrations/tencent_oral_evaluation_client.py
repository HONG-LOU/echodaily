from __future__ import annotations

import asyncio
import base64
import binascii
import re
from dataclasses import dataclass
from typing import Literal
from uuid import uuid4

from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.soe.v20180724 import models, soe_client

from app.core.config import get_settings
from app.core.errors import BadRequestError, IntegrationError, ServiceUnavailableError

type AudioFormat = Literal["mp3", "wav", "pcm", "speex"]

VOICE_FILE_TYPE_MAP: dict[AudioFormat, int] = {
    "pcm": 1,
    "wav": 2,
    "mp3": 3,
    "speex": 4,
}

MATCH_TAG_MATCHED = 0
MATCH_TAG_INSERTED = 1
MATCH_TAG_MISSING = 2
MATCH_TAG_MISREAD = 3
MATCH_TAG_UNRECORDED = 4


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
    async def evaluate_sentence(
        self,
        *,
        reference_text: str,
        audio_base64: str,
        audio_format: AudioFormat,
    ) -> OralEvaluationResult:
        return await asyncio.to_thread(
            self._evaluate_sentence_sync,
            reference_text,
            audio_base64,
            audio_format,
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

        if audio_format not in VOICE_FILE_TYPE_MAP:
            raise BadRequestError("暂不支持该音频格式。", code="unsupported_audio_format")

        self._validate_base64_payload(audio_base64)

        session_id = f"assessment-{uuid4().hex}"
        request = models.TransmitOralProcessWithInitRequest()
        request.SeqId = 1
        request.IsEnd = 1
        request.VoiceFileType = VOICE_FILE_TYPE_MAP[audio_format]
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

    def _validate_base64_payload(self, audio_base64: str) -> None:
        if not audio_base64.strip():
            raise BadRequestError("录音内容不能为空。", code="empty_audio_payload")

        try:
            base64.b64decode(audio_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise BadRequestError("录音数据不是有效的 Base64 内容。", code="invalid_audio") from exc

    def _build_word(self, item: models.WordRsp) -> EvaluatedWord:
        phone_infos = item.PhoneInfos or []
        expected_phones = [
            phone.ReferencePhone or phone.Phone
            for phone in phone_infos
            if (phone.ReferencePhone or phone.Phone)
        ]
        observed_phones = [
            phone.Phone or phone.ReferencePhone
            for phone in phone_infos
            if (phone.Phone or phone.ReferencePhone)
        ]
        stress_mismatch_count = sum(
            1
            for phone in phone_infos
            if phone.Stress is not None
            and phone.DetectedStress is not None
            and bool(phone.Stress) != bool(phone.DetectedStress)
        )

        return EvaluatedWord(
            word=(item.Word or "").strip(),
            match_tag=int(item.MatchTag or 0),
            pronunciation_score=self._normalize_percentage(item.PronAccuracy),
            fluency_score=self._normalize_unit_score(item.PronFluency),
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

    def _map_sdk_exception(self, exc: TencentCloudSDKException) -> IntegrationError:
        error_code = exc.get_code() or ""
        if error_code in {
            "InvalidCredential",
            "AuthFailure.SecretIdNotFound",
            "AuthFailure.SignatureFailure",
        }:
            return ServiceUnavailableError(
                "腾讯云评测凭证无效，请检查 SecretId / SecretKey 配置。",
                code="speech_assessment_invalid_credentials",
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
