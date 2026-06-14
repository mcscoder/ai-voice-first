from __future__ import annotations

from pathlib import Path

from app.core.config import MemoryConfig
from app.services.memory.service import MemoryService


def test_memory_config_uses_gemini_and_qwen_huggingface(tmp_path: Path) -> None:
    memory_config = MemoryConfig(data_dir=tmp_path)

    mem0_config = memory_config.to_mem0_config()

    assert mem0_config["llm"] == {
        "provider": "gemini",
        "config": {
            "model": memory_config.llm_model,
            "api_key": memory_config.llm_api_key,
            "temperature": memory_config.llm_temperature,
            "max_tokens": memory_config.llm_max_tokens,
        },
    }
    assert mem0_config["embedder"] == {
        "provider": "huggingface",
        "config": {
            "model": "Qwen/Qwen3-Embedding-0.6B",
            "embedding_dims": 1024,
        },
    }
    assert mem0_config["vector_store"]["config"]["embedding_model_dims"] == 1024
    assert mem0_config["history_db_path"] == str(tmp_path / "history.db")


def test_memory_service_delegates_add_and_search_without_eager_loading(
    tmp_path: Path,
) -> None:
    class FakeMemory:
        def __init__(self) -> None:
            self.add_calls = []
            self.search_calls = []

        def add(self, *args, **kwargs) -> dict:
            self.add_calls.append((args, kwargs))
            return {"results": [{"memory": "remembered"}]}

        def search(self, *args, **kwargs) -> dict:
            self.search_calls.append((args, kwargs))
            return {"results": [{"memory": "remembered", "score": 1.0}]}

    service = MemoryService(MemoryConfig(data_dir=tmp_path))
    fake_memory = FakeMemory()
    service._memory = fake_memory

    add_result = service.add("Remember that I like Vietnamese coffee.", user_id="u1")
    search_result = service.search("coffee", user_id="u1", limit=5)

    assert add_result == {"results": [{"memory": "remembered"}]}
    assert search_result == {"results": [{"memory": "remembered", "score": 1.0}]}
    assert fake_memory.add_calls == [
        (
            ("Remember that I like Vietnamese coffee.",),
            {
                "user_id": "u1",
                "agent_id": None,
                "run_id": None,
                "metadata": None,
                "infer": True,
            },
        ),
    ]
    assert fake_memory.search_calls == [
        (
            ("coffee",),
            {
                "user_id": "u1",
                "agent_id": None,
                "run_id": None,
                "limit": 5,
                "filters": None,
            },
        ),
    ]
