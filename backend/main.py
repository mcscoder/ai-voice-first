from __future__ import annotations

import os
import tempfile
from contextlib import asynccontextmanager
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from faster_whisper import WhisperModel
from dotenv import load_dotenv


load_dotenv()


def env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class AudioTranscriptionError(Exception):
    pass


class BackendTranscriptionError(Exception):
    pass


class LanguageOption(StrEnum):
    AUTO = "auto"
    AF = "af"
    AM = "am"
    AR = "ar"
    AS = "as"
    AZ = "az"
    BA = "ba"
    BE = "be"
    BG = "bg"
    BN = "bn"
    BO = "bo"
    BR = "br"
    BS = "bs"
    CA = "ca"
    CS = "cs"
    CY = "cy"
    DA = "da"
    DE = "de"
    EL = "el"
    EN = "en"
    ES = "es"
    ET = "et"
    EU = "eu"
    FA = "fa"
    FI = "fi"
    FO = "fo"
    FR = "fr"
    GL = "gl"
    GU = "gu"
    HA = "ha"
    HAW = "haw"
    HE = "he"
    HI = "hi"
    HR = "hr"
    HT = "ht"
    HU = "hu"
    HY = "hy"
    ID = "id"
    IS = "is"
    IT = "it"
    JA = "ja"
    JW = "jw"
    KA = "ka"
    KK = "kk"
    KM = "km"
    KN = "kn"
    KO = "ko"
    LA = "la"
    LB = "lb"
    LN = "ln"
    LO = "lo"
    LT = "lt"
    LV = "lv"
    MG = "mg"
    MI = "mi"
    MK = "mk"
    ML = "ml"
    MN = "mn"
    MR = "mr"
    MS = "ms"
    MT = "mt"
    MY = "my"
    NE = "ne"
    NL = "nl"
    NN = "nn"
    NO = "no"
    OC = "oc"
    PA = "pa"
    PL = "pl"
    PS = "ps"
    PT = "pt"
    RO = "ro"
    RU = "ru"
    SA = "sa"
    SD = "sd"
    SI = "si"
    SK = "sk"
    SL = "sl"
    SN = "sn"
    SO = "so"
    SQ = "sq"
    SR = "sr"
    SU = "su"
    SV = "sv"
    SW = "sw"
    TA = "ta"
    TE = "te"
    TG = "tg"
    TH = "th"
    TK = "tk"
    TL = "tl"
    TR = "tr"
    TT = "tt"
    UK = "uk"
    UR = "ur"
    UZ = "uz"
    VI = "vi"
    YI = "yi"
    YO = "yo"
    ZH = "zh"


class TranscriptionService:
    def __init__(self) -> None:
        self.model_name = os.getenv("WHISPER_MODEL", "base")
        self.device = os.getenv("WHISPER_DEVICE", "cpu")
        self.compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
        self._model: WhisperModel | None = None

    def load_model(self) -> WhisperModel:
        try:
            if self._model is None:
                self._model = WhisperModel(
                    self.model_name,
                    device=self.device,
                    compute_type=self.compute_type,
                )
            return self._model
        except Exception as exc:
            raise BackendTranscriptionError(
                "Failed to initialize the transcription model: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

    def transcribe(
        self,
        file_path: str,
        language: LanguageOption = LanguageOption.AUTO,
    ) -> dict[str, object]:
        try:
            model = self.load_model()
        except BackendTranscriptionError:
            raise

        try:
            transcribe_kwargs: dict[str, str] = {}
            if language is not LanguageOption.AUTO:
                transcribe_kwargs["language"] = language.value

            segments, info = model.transcribe(file_path, **transcribe_kwargs)
            text = " ".join(segment.text.strip() for segment in segments).strip()
        except RuntimeError as exc:
            raise BackendTranscriptionError(
                "Transcription backend failed: "
                f"{type(exc).__name__}: {exc}"
            ) from exc
        except Exception as exc:
            raise AudioTranscriptionError(
                "Unable to decode or transcribe the provided audio file: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        return {
            "text": text,
            "requested_language": language.value,
            "model": self.model_name,
            "language": info.language,
            "language_probability": info.language_probability,
            "duration_seconds": info.duration,
        }


service = TranscriptionService()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if env_flag("WHISPER_LOAD_ON_STARTUP", True):
        service.load_model()
    yield


app = FastAPI(title="Voice to Text API", version="0.1.0", lifespan=lifespan)


@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Annotated[LanguageOption, Form()] = LanguageOption.AUTO,
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

        result = service.transcribe(temp_path, language=language)
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


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
