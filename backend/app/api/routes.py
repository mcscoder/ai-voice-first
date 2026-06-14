import asyncio

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.asr import asr_service


# Keep base routes together until the API surface grows enough to split by feature.
router = APIRouter()


@router.get("/")
def read_root() -> dict[str, str]:
    return {"message": "AI Voice First backend is running"}


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/asr")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str | None = Form(None),
) -> dict[str, str | None]:
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    result = await asyncio.to_thread(
        asr_service.transcribe,
        audio_bytes,
        language,
    )

    return {
        "text": result.text,
        "language": result.language,
        "model": result.model,
        "filename": file.filename,
        "content_type": file.content_type,
    }
