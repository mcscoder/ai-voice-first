from app.core.config import MemoryConfig
from app.services.asr.service import AsrService


def test_asr_loads_qwen_with_4bit_quantization(monkeypatch) -> None:
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

    model = AsrService(model_name="test-qwen-asr", device="auto").load_model()

    assert model is loaded_model
    assert calls["model_name"] == "test-qwen-asr"
    kwargs = calls["kwargs"]
    assert isinstance(kwargs, dict)
    assert kwargs["device_map"] == "auto"
    quantization_config = kwargs["quantization_config"]
    assert quantization_config.load_in_4bit is True
    assert str(quantization_config.bnb_4bit_compute_dtype) == "torch.float16"
    assert quantization_config.bnb_4bit_quant_type == "nf4"
    assert quantization_config.bnb_4bit_use_double_quant is True


def test_memory_config_passes_4bit_quantization_to_huggingface_embedder() -> None:
    mem0_config = MemoryConfig().to_mem0_config()

    embedder_config = mem0_config["embedder"]["config"]
    sentence_transformer_kwargs = embedder_config["model_kwargs"]
    model_kwargs = sentence_transformer_kwargs["model_kwargs"]

    assert model_kwargs["device_map"] == "auto"
    quantization_config = model_kwargs["quantization_config"]
    assert quantization_config.load_in_4bit is True
    assert str(quantization_config.bnb_4bit_compute_dtype) == "torch.float16"
    assert quantization_config.bnb_4bit_quant_type == "nf4"
    assert quantization_config.bnb_4bit_use_double_quant is True


def test_memory_config_uses_deepseek_llm() -> None:
    mem0_config = MemoryConfig().to_mem0_config()

    llm_config = mem0_config["llm"]
    assert llm_config["provider"] == "deepseek"
    assert llm_config["config"]["model"] == "deepseek-v4-flash"
    assert llm_config["config"]["api_key"] is None
    assert llm_config["config"]["deepseek_base_url"] == "https://api.deepseek.com"
