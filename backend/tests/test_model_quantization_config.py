import pytest

from app.core.config import MemoryConfig
from app.services.asr.service import AsrService, UnsupportedAsrLanguageError


def load_asr_model_kwargs(monkeypatch, quantization_level: str) -> dict[str, object]:
    calls: dict[str, object] = {}
    loaded_model = object()

    def from_pretrained(model_name: str, **kwargs: object) -> object:
        calls["model_name"] = model_name
        calls["kwargs"] = kwargs
        return loaded_model

    monkeypatch.setattr(
        "app.services.asr.service.Qwen3ASRModel.from_pretrained",
        from_pretrained,
    )

    model = AsrService(
        model_name="test-qwen-asr",
        device="auto",
        quantization_level=quantization_level,
    ).load_model()

    assert model is loaded_model
    assert calls["model_name"] == "test-qwen-asr"
    kwargs = calls["kwargs"]
    assert isinstance(kwargs, dict)
    assert kwargs["device_map"] == "auto"
    return kwargs


def get_memory_model_kwargs(quantization_level: str | None = None) -> dict[str, object]:
    if quantization_level is None:
        mem0_config = MemoryConfig().to_mem0_config()
    else:
        mem0_config = MemoryConfig(
            embedding_quantization_level=quantization_level
        ).to_mem0_config()

    embedder_config = mem0_config["embedder"]["config"]
    sentence_transformer_kwargs = embedder_config["model_kwargs"]
    model_kwargs = sentence_transformer_kwargs["model_kwargs"]

    assert model_kwargs["device_map"] == "auto"
    return model_kwargs


def assert_4bit_quantization(quantization_config: object, quant_type: str) -> None:
    assert quantization_config.load_in_4bit is True
    assert str(quantization_config.bnb_4bit_compute_dtype) == "torch.float16"
    assert quantization_config.bnb_4bit_quant_type == quant_type


def test_asr_loads_qwen_with_default_8bit_quantization(monkeypatch) -> None:
    kwargs = load_asr_model_kwargs(monkeypatch, quantization_level="int8")

    quantization_config = kwargs["quantization_config"]
    assert quantization_config.load_in_8bit is True


def test_asr_can_disable_quantization(monkeypatch) -> None:
    kwargs = load_asr_model_kwargs(monkeypatch, quantization_level="none")

    assert "quantization_config" not in kwargs


def test_asr_supports_4bit_quantization_levels(monkeypatch) -> None:
    nf4_kwargs = load_asr_model_kwargs(monkeypatch, quantization_level="int4-nf4")
    fp4_kwargs = load_asr_model_kwargs(monkeypatch, quantization_level="int4-fp4")

    assert_4bit_quantization(nf4_kwargs["quantization_config"], quant_type="nf4")
    assert_4bit_quantization(fp4_kwargs["quantization_config"], quant_type="fp4")


def test_asr_defaults_to_vietnamese_when_language_is_missing() -> None:
    assert AsrService().normalize_language(None) == "Vietnamese"


def test_asr_rejects_english_language() -> None:
    with pytest.raises(UnsupportedAsrLanguageError):
        AsrService().normalize_language("en")


def test_memory_config_disables_embedding_quantization_by_default() -> None:
    model_kwargs = get_memory_model_kwargs()

    assert "quantization_config" not in model_kwargs


def test_memory_config_can_pass_8bit_quantization_to_huggingface_embedder() -> None:
    model_kwargs = get_memory_model_kwargs(quantization_level="int8")

    quantization_config = model_kwargs["quantization_config"]
    assert quantization_config.load_in_8bit is True


def test_memory_config_can_disable_embedding_quantization() -> None:
    model_kwargs = get_memory_model_kwargs(quantization_level="none")

    assert "quantization_config" not in model_kwargs


def test_memory_config_supports_4bit_embedding_quantization_levels() -> None:
    nf4_model_kwargs = get_memory_model_kwargs(quantization_level="int4-nf4")
    fp4_model_kwargs = get_memory_model_kwargs(quantization_level="int4-fp4")

    assert_4bit_quantization(
        nf4_model_kwargs["quantization_config"],
        quant_type="nf4",
    )
    assert_4bit_quantization(
        fp4_model_kwargs["quantization_config"],
        quant_type="fp4",
    )


def test_memory_config_uses_deepseek_llm() -> None:
    mem0_config = MemoryConfig().to_mem0_config()

    llm_config = mem0_config["llm"]
    assert llm_config["provider"] == "deepseek"
    assert llm_config["config"]["model"] == "deepseek-v4-flash"
    assert llm_config["config"]["api_key"] is None
    assert llm_config["config"]["deepseek_base_url"] == "https://api.deepseek.com/beta"


def test_memory_config_disables_deepseek_thinking_by_default(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_THINKING", raising=False)

    memory_config = MemoryConfig()

    assert memory_config.llm_thinking == "disabled"
    assert memory_config.to_deepseek_extra_body() == {
        "thinking": {"type": "disabled"}
    }


def test_memory_config_can_enable_deepseek_thinking(monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_THINKING", "enabled")

    memory_config = MemoryConfig()

    assert memory_config.llm_thinking == "enabled"
    assert memory_config.to_deepseek_extra_body() == {"thinking": {"type": "enabled"}}


def test_memory_config_rejects_invalid_deepseek_thinking(monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_THINKING", "maybe")

    with pytest.raises(ValueError, match="DEEPSEEK_THINKING"):
        MemoryConfig()
