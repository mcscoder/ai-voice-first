from __future__ import annotations

import os
from enum import StrEnum

from dotenv import load_dotenv
from faster_whisper import WhisperModel


load_dotenv()


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
