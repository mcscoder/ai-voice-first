from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from transcription_service import (
    AudioTranscriptionError,
    BackendTranscriptionError,
    transcription_service,
)


router = APIRouter()


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
) -> dict[str, object]:
    suffix = Path(file.filename or "").suffix or ".bin"
    bytes_written = 0
    temp_path: str | None = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_path = temp_file.name

            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                temp_file.write(chunk)
                bytes_written += len(chunk)

        if bytes_written == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        result = await transcription_service.transcribe(temp_path)
        return {
            **result,
            "filename": file.filename,
            "content_type": file.content_type,
        }
    except AudioTranscriptionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except BackendTranscriptionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        await file.close()
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
