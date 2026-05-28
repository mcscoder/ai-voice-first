from __future__ import annotations

import os
from enum import StrEnum
from typing import Any

from dotenv import load_dotenv
import soundfile as sf
import sherpa_onnx
from huggingface_hub import hf_hub_download


load_dotenv()

REPO_ID = "g-group-ai-lab/gipformer-65M-rnnt"
SAMPLE_RATE = 16000
FEATURE_DIM = 80
ONNX_FILES = {
    "fp32": {
        "encoder": "encoder-epoch-35-avg-6.onnx",
        "decoder": "decoder-epoch-35-avg-6.onnx",
        "joiner": "joiner-epoch-35-avg-6.onnx",
    },
    "int8": {
        "encoder": "encoder-epoch-35-avg-6.int8.onnx",
        "decoder": "decoder-epoch-35-avg-6.int8.onnx",
        "joiner": "joiner-epoch-35-avg-6.int8.onnx",
    },
}


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
        self.model_name = REPO_ID
        self.precision = os.getenv("ASR_PRECISION", "fp32") .lower()
        self.num_threads = int(os.getenv("ASR_NUM_THREADS", "4"))
        self.provider = os.getenv("ASR_PROVIDER", "cpu").strip().lower()
        self.decoding_method = "modified_beam_search"
        self._model: Any | None = None

    def _download_model_paths(self) -> dict[str, str]:
        precision = "int8" if self.precision == "int8" else "fp32"
        file_map = ONNX_FILES[precision]

        paths: dict[str, str] = {}
        for key, filename in file_map.items():
            paths[key] = hf_hub_download(repo_id=self.model_name, filename=filename)
        paths["tokens"] = hf_hub_download(repo_id=self.model_name, filename="tokens.txt")
        return paths

    def load_model(self) -> Any:
        try:
            if self._model is None:
                model_paths = self._download_model_paths()
                self._model = sherpa_onnx.OfflineRecognizer.from_transducer(
                    encoder=model_paths["encoder"],
                    decoder=model_paths["decoder"],
                    joiner=model_paths["joiner"],
                    tokens=model_paths["tokens"],
                    num_threads=self.num_threads,
                    sample_rate=SAMPLE_RATE,
                    feature_dim=FEATURE_DIM,
                    decoding_method=self.decoding_method,
                    provider=self.provider,
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
            samples, sample_rate = sf.read(file_path, dtype="float32")
            if samples.ndim > 1:
                samples = samples.mean(axis=1)

            stream = model.create_stream()
            stream.accept_waveform(sample_rate, samples)
            model.decode_streams([stream])
            text = stream.result.text.strip()
            duration_seconds = float(sf.info(file_path).duration)
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
            "language": "vi",
            "language_probability": None,
            "duration_seconds": duration_seconds,
        }


transcription_service = TranscriptionService()
