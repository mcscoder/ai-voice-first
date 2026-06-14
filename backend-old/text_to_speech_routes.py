from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, field_validator

from text_to_speech_service import (
    MAX_TEXT_LENGTH,
    TextToSpeechNoAudioError,
    synthesize_speech,
)


router = APIRouter()


class TextToSpeechRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("Text must not be empty")
        if len(text) > MAX_TEXT_LENGTH:
            raise ValueError(f"Text must be at most {MAX_TEXT_LENGTH} characters")
        return text


@router.post(
    "/tts",
    responses={
        200: {
            "content": {
                "audio/mpeg": {
                    "schema": {"type": "string", "format": "binary"},
                },
            },
            "description": "Generated MP3 audio",
        },
    },
    response_class=Response,
)
async def text_to_speech(request: TextToSpeechRequest) -> Response:
    try:
        audio = await synthesize_speech(request.text)
    except TextToSpeechNoAudioError as exc:
        raise HTTPException(
            status_code=502,
            detail="Text-to-speech service returned no audio.",
        ) from exc

    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={"Content-Disposition": 'attachment; filename="speech.mp3"'},
    )
