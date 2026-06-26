from app.core.config import MemoryConfig
from app.services.memory.prompt import build_response_messages
from app.services.memory.service import MemorySearchResult, MemoryService


class FakeLlm:
    def __init__(self, response: str) -> None:
        self.response = response
        self.messages: list[dict[str, str]] | None = None
        self.kwargs: dict[str, object] | None = None
        self.client: object | None = None

    def generate_response(self, messages: list[dict[str, str]], **kwargs: object) -> str:
        self.messages = messages
        self.kwargs = kwargs
        return self.response


class FakeMemory:
    def __init__(
        self,
        response: str,
        memories: list[str] | None = None,
        search_results: list[dict[str, object]] | None = None,
        add_result: dict[str, object] | None = None,
    ) -> None:
        self.llm = FakeLlm(response)
        self.memories = memories or []
        self.search_results = search_results
        self.add_result = add_result
        self.added_messages: list[dict[str, str]] | None = None
        self.added_user_id: str | None = None

    def search(self, query: str, user_id: str, limit: int) -> dict[str, object]:
        if self.search_results is not None:
            return {"results": self.search_results}
        return {"results": [{"memory": memory} for memory in self.memories]}

    def add(self, messages: list[dict[str, str]], user_id: str) -> dict[str, object] | None:
        self.added_messages = messages
        self.added_user_id = user_id
        return self.add_result


class FakeMemoryService(MemoryService):
    def __init__(
        self,
        memory: FakeMemory,
        memory_config: MemoryConfig | None = None,
    ) -> None:
        self.memory = memory
        self.memory_config = memory_config or MemoryConfig()

    def load_memory(self) -> FakeMemory:
        return self.memory


class FakeStreamDelta:
    def __init__(self, content: str | None) -> None:
        self.content = content


class FakeStreamChoice:
    def __init__(self, content: str | None) -> None:
        self.delta = FakeStreamDelta(content)


class FakeStreamChunk:
    def __init__(self, content: str | None) -> None:
        self.choices = [FakeStreamChoice(content)]


class FakeChatCompletions:
    def __init__(self) -> None:
        self.kwargs: dict[str, object] | None = None

    def create(self, **kwargs: object) -> list[FakeStreamChunk]:
        self.kwargs = kwargs
        return [
            FakeStreamChunk("Xin"),
            FakeStreamChunk(None),
            FakeStreamChunk(" chào"),
        ]


class FakeChat:
    def __init__(self, completions: FakeChatCompletions) -> None:
        self.completions = completions


class FakeDeepSeekClient:
    def __init__(self, completions: FakeChatCompletions) -> None:
        self.chat = FakeChat(completions)


def test_memory_prompt_requires_plain_spoken_text() -> None:
    memory = FakeMemory("Sure, I can help with that.")
    service = FakeMemoryService(memory)

    service.respond("Can you help me?", "test-user")

    assert memory.llm.messages is not None
    system_prompt = memory.llm.messages[0]["content"]
    assert "plain spoken text only" in system_prompt
    assert "Do not use Markdown" in system_prompt
    assert "real human assistant" in system_prompt


def test_memory_respond_passes_deepseek_thinking_extra_body() -> None:
    memory = FakeMemory("Tôi nghe rồi.")
    service = FakeMemoryService(memory, MemoryConfig(llm_thinking="disabled"))

    service.respond("Xin chào", "test-user")

    assert memory.llm.kwargs == {"extra_body": {"thinking": {"type": "disabled"}}}


def test_memory_stream_response_passes_deepseek_thinking_extra_body() -> None:
    memory = FakeMemory("unused")
    completions = FakeChatCompletions()
    memory.llm.client = FakeDeepSeekClient(completions)
    service = FakeMemoryService(memory, MemoryConfig(llm_thinking="enabled"))

    chunks = list(
        service.stream_response(
            "Xin chào",
            [],
            [{"role": "user", "content": "Xin chào"}],
        )
    )

    assert chunks == ["Xin", " chào"]
    assert completions.kwargs is not None
    assert completions.kwargs["model"] == "deepseek-v4-flash"
    assert completions.kwargs["stream"] is True
    assert completions.kwargs["extra_body"] == {"thinking": {"type": "enabled"}}


def test_memory_response_cleans_markdown_before_saving_and_returning() -> None:
    memory = FakeMemory(
        """
        ## Here's the plan
        - **Review** your notes
        1. Open `VocalMind`
        > Use [today's list](https://example.com)
        """,
        memories=["The user reviews notes every morning."],
    )
    service = FakeMemoryService(memory)

    reply = service.respond("What should I do today?", "test-user")

    expected = "Here's the plan Review your notes Open VocalMind Use today's list"
    assert reply.text == expected
    assert memory.added_messages == [
        {"role": "user", "content": "What should I do today?"},
        {"role": "assistant", "content": expected},
    ]
    assert memory.added_user_id == "test-user"


def test_memory_search_results_include_scores() -> None:
    first_result = {
        "id": "memory-id",
        "memory": "User likes short answers.",
        "score": 0.87321,
        "user_id": "test-user",
        "categories": ["personal_info"],
        "created_at": "2026-06-25T04:08:26+00:00",
        "updated_at": "2026-06-25T05:40:29+00:00",
        "metadata": {"topic": "preferences"},
    }
    memory = FakeMemory(
        "unused",
        search_results=[
            first_result,
            {"memory": "Invalid score is still shown.", "score": "bad"},
        ],
    )
    service = FakeMemoryService(memory)

    results = service.search_memory_results("Hello", "test-user")
    assert results == [
        MemorySearchResult(
            id="memory-id",
            memory="User likes short answers.",
            score=0.87321,
            user_id="test-user",
            categories=["personal_info"],
            created_at="2026-06-25T04:08:26+00:00",
            updated_at="2026-06-25T05:40:29+00:00",
            metadata={"topic": "preferences"},
        ),
        MemorySearchResult(
            memory="Invalid score is still shown.",
            score=None,
        ),
    ]
    assert [item.memory for item in results] == [
        "User likes short answers.",
        "Invalid score is still shown.",
    ]


def test_memory_search_result_from_mem0_preserves_fields_for_telemetry() -> None:
    result = MemorySearchResult.from_mem0(
        {
            "id": "mem_123abc",
            "memory": "Name is Alex. Enjoys basketball and gaming.",
            "user_id": "alex",
            "categories": ["personal_info"],
            "created_at": "2025-10-22T04:40:22.864647-07:00",
            "score": 0.89,
            "metadata": {"source": "mem0"},
            "custom_field": "custom-value",
        }
    )

    assert result.as_telemetry() == {
        "id": "mem_123abc",
        "memory": "Name is Alex. Enjoys basketball and gaming.",
        "user_id": "alex",
        "categories": ["personal_info"],
        "created_at": "2025-10-22T04:40:22.864647-07:00",
        "score": 0.89,
        "metadata": {"source": "mem0"},
        "custom_field": "custom-value",
    }


def test_memory_prompt_uses_compact_csv_context() -> None:
    memory = FakeMemory(
        "Tôi nhớ rồi.",
        search_results=[
            {
                "id": "memory-id",
                "memory": "Nguyên nợ tôi năm mươi ngàn hôm qua chưa trả.",
                "score": 0.82,
                "user_id": "test-user",
                "categories": ["finance", "debt"],
                "created_at": "2026-06-25T04:08:26+00:00",
                "updated_at": "2026-06-25T05:40:29+00:00",
                "metadata": {"topic": "debt"},
            }
        ],
    )
    service = FakeMemoryService(memory)

    service.respond("Hôm nay Nguyên trả chưa?", "test-user")

    assert memory.llm.messages is not None
    user_prompt = memory.llm.messages[1]["content"]
    assert "Current local time:" in user_prompt
    assert "Current UTC time:" in user_prompt
    assert "Relevant memories CSV:" in user_prompt
    assert "memory,created_at,updated_at" in user_prompt
    assert "id,memory,user_id,categories,created_at,updated_at,score" not in user_prompt
    assert "hôm qua" in user_prompt
    assert (
        "Nguyên nợ tôi năm mươi ngàn hôm qua chưa trả.,"
        "2026-06-25T04:08:26+00:00,2026-06-25T05:40:29+00:00"
    ) in user_prompt
    assert "memory-id" not in user_prompt
    assert "test-user" not in user_prompt
    assert "finance|debt" not in user_prompt
    assert "0.82" not in user_prompt
    assert "metadata:" not in user_prompt
    assert "created_at:" not in user_prompt


def test_memory_build_response_messages_quotes_csv_values() -> None:
    messages = build_response_messages(
        "What changed?",
        [
            MemorySearchResult(
                id="memory-id",
                memory="User discussed a debt, with comma.",
                score=0.91,
                user_id="test-user",
            )
        ],
    )

    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "system"
    assert messages[2] == {"role": "user", "content": "What changed?"}
    context_prompt = messages[1]["content"]
    assert '"User discussed a debt, with comma.",,' in context_prompt
    assert "memory-id" not in context_prompt
    assert "test-user" not in context_prompt
    assert "0.91" not in context_prompt


def test_memory_persist_returns_structured_memory_actions() -> None:
    memory = FakeMemory(
        "unused",
        add_result={
            "results": [
                {
                    "id": "memory-id",
                    "memory": "Nguyên nợ tôi năm mươi ngàn.",
                    "event": "UPDATE",
                    "previous_memory": "Nguyên nợ tôi tiền.",
                }
            ]
        },
    )
    service = FakeMemoryService(memory)

    result = service.persist_conversation("query", "response", "test-user")

    assert result.actions == [
        {
            "id": "memory-id",
            "memory": "Nguyên nợ tôi năm mươi ngàn.",
            "event": "UPDATE",
            "previous_memory": "Nguyên nợ tôi tiền.",
        }
    ]
    assert result.action_counts == {"UPDATE": 1}
    assert result.raw_result == memory.add_result


def test_memory_persist_captures_noop_actions_from_raw_mem0_result() -> None:
    memory = FakeMemory(
        "unused",
        add_result={
            "results": [
                {
                    "id": "1",
                    "text": "Đang dự định in lại tài liệu",
                    "event": "NONE",
                }
            ]
        },
    )
    service = FakeMemoryService(memory)

    result = service.persist_conversation("query", "response", "test-user")

    assert result.actions == [
        {
            "id": "1",
            "memory": "Đang dự định in lại tài liệu",
            "event": "NONE",
        }
    ]
    assert result.action_counts == {"NONE": 1}
