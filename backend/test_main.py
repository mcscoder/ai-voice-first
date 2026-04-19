from __future__ import annotations

from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import patch

from fastapi import HTTPException

import main


class DummyUploadFile:
    def __init__(
        self,
        *,
        filename: str,
        content_type: str,
        payload: bytes,
    ) -> None:
        self.filename = filename
        self.content_type = content_type
        self._payload = payload
        self._read = False
        self.closed = False

    async def read(self, _: int = -1) -> bytes:
        if self._read:
            return b""
        self._read = True
        return self._payload

    async def close(self) -> None:
        self.closed = True


class OpenAPITests(TestCase):
    def test_transcribe_schema_only_requires_file(self) -> None:
        schema = main.app.openapi()
        body_ref = schema["paths"]["/transcribe"]["post"]["requestBody"]["content"][
            "multipart/form-data"
        ]["schema"]["$ref"]
        body_name = body_ref.rsplit("/", maxsplit=1)[-1]
        body_schema = schema["components"]["schemas"][body_name]

        self.assertEqual(list(body_schema["properties"].keys()), ["file"])
        self.assertEqual(body_schema["required"], ["file"])
        self.assertNotIn("LanguageOption", schema["components"]["schemas"])


class RouteTests(IsolatedAsyncioTestCase):
    async def test_transcribe_audio_success(self) -> None:
        upload = DummyUploadFile(
            filename="sample.wav",
            content_type="audio/wav",
            payload=b"not-empty",
        )

        with patch.object(
            main.service,
            "transcribe",
            return_value={"text": "xin chao", "model": main.PUBLIC_MODEL_NAME},
        ) as transcribe:
            response = await main.transcribe_audio(upload)

        transcribe.assert_called_once()
        self.assertEqual(response["text"], "xin chao")
        self.assertEqual(response["model"], main.PUBLIC_MODEL_NAME)
        self.assertEqual(response["filename"], "sample.wav")
        self.assertEqual(response["content_type"], "audio/wav")
        self.assertTrue(upload.closed)

    async def test_transcribe_audio_rejects_empty_upload(self) -> None:
        upload = DummyUploadFile(
            filename="empty.wav",
            content_type="audio/wav",
            payload=b"",
        )

        with self.assertRaises(HTTPException) as context:
            await main.transcribe_audio(upload)

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Uploaded file is empty.")
        self.assertTrue(upload.closed)

    async def test_transcribe_audio_maps_audio_errors_to_400(self) -> None:
        upload = DummyUploadFile(
            filename="broken.wav",
            content_type="audio/wav",
            payload=b"bad-audio",
        )

        with patch.object(
            main.service,
            "transcribe",
            side_effect=main.AudioTranscriptionError("bad audio"),
        ):
            with self.assertRaises(HTTPException) as context:
                await main.transcribe_audio(upload)

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "bad audio")
        self.assertTrue(upload.closed)

    async def test_transcribe_audio_maps_backend_errors_to_500(self) -> None:
        upload = DummyUploadFile(
            filename="broken.wav",
            content_type="audio/wav",
            payload=b"bad-audio",
        )

        with patch.object(
            main.service,
            "transcribe",
            side_effect=main.BackendTranscriptionError("backend down"),
        ):
            with self.assertRaises(HTTPException) as context:
                await main.transcribe_audio(upload)

        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(context.exception.detail, "backend down")
        self.assertTrue(upload.closed)


class ServiceTests(TestCase):
    def test_extract_transcript_text_supports_hypotheses(self) -> None:
        transcriptions = [SimpleNamespace(text=" xin chao ")]
        self.assertEqual(main.extract_transcript_text(transcriptions), "xin chao")

    def test_extract_transcript_text_supports_plain_strings(self) -> None:
        transcriptions = [" xin chao "]
        self.assertEqual(main.extract_transcript_text(transcriptions), "xin chao")
