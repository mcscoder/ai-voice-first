import logging

from app.services.memory.service import MemorySearchResult, MemoryService


class FakeLlm:
    def __init__(self, response: str) -> None:
        self.response = response
        self.messages: list[dict[str, str]] | None = None

    def generate_response(self, messages: list[dict[str, str]]) -> str:
        self.messages = messages
        return self.response


class FakeMemory:
    def __init__(
        self,
        response: str,
        memories: list[str] | None = None,
        search_results: list[dict[str, object]] | None = None,
        add_result: dict[str, object] | None = None,
        logged_actions: list[dict[str, object]] | None = None,
    ) -> None:
        self.llm = FakeLlm(response)
        self.memories = memories or []
        self.search_results = search_results
        self.add_result = add_result
        self.logged_actions = logged_actions or []
        self.added_messages: list[dict[str, str]] | None = None
        self.added_user_id: str | None = None

    def search(self, query: str, user_id: str, limit: int) -> dict[str, object]:
        if self.search_results is not None:
            return {"results": self.search_results}
        return {"results": [{"memory": memory} for memory in self.memories]}

    def add(self, messages: list[dict[str, str]], user_id: str) -> None:
        self.added_messages = messages
        self.added_user_id = user_id
        logger = logging.getLogger("mem0.memory.main")
        for action in self.logged_actions:
            logger.info(action)
        return self.add_result


class FakeMemoryService(MemoryService):
    def __init__(self, memory: FakeMemory) -> None:
        self.memory = memory

    def load_memory(self) -> FakeMemory:
        return self.memory


def test_memory_prompt_requires_plain_spoken_text() -> None:
    memory = FakeMemory("Sure, I can help with that.")
    service = FakeMemoryService(memory)

    service.respond("Can you help me?", "test-user")

    assert memory.llm.messages is not None
    system_prompt = memory.llm.messages[0]["content"]
    assert "plain spoken text only" in system_prompt
    assert "Do not use Markdown" in system_prompt
    assert "real human assistant" in system_prompt


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
    memory = FakeMemory(
        "unused",
        search_results=[
            {"memory": "User likes short answers.", "score": 0.87321},
            {"memory": "Invalid score is still shown.", "score": "bad"},
        ],
    )
    service = FakeMemoryService(memory)

    assert service.search_memory_results("Hello", "test-user") == [
        MemorySearchResult(memory="User likes short answers.", score=0.87321),
        MemorySearchResult(memory="Invalid score is still shown.", score=None),
    ]
    assert service.search_memories("Hello", "test-user") == [
        "User likes short answers.",
        "Invalid score is still shown.",
    ]


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


def test_memory_persist_captures_noop_actions_from_structured_mem0_logs() -> None:
    memory = FakeMemory(
        "unused",
        add_result={"results": []},
        logged_actions=[
            {
                "id": "1",
                "text": "Đang dự định in lại tài liệu",
                "event": "NONE",
            }
        ],
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
