from app.services.memory.service import MemoryService


class FakeLlm:
    def __init__(self, response: str) -> None:
        self.response = response
        self.messages: list[dict[str, str]] | None = None

    def generate_response(self, messages: list[dict[str, str]]) -> str:
        self.messages = messages
        return self.response


class FakeMemory:
    def __init__(self, response: str, memories: list[str] | None = None) -> None:
        self.llm = FakeLlm(response)
        self.memories = memories or []
        self.added_messages: list[dict[str, str]] | None = None
        self.added_user_id: str | None = None

    def search(self, query: str, user_id: str, limit: int) -> dict[str, object]:
        return {"results": [{"memory": memory} for memory in self.memories]}

    def add(self, messages: list[dict[str, str]], user_id: str) -> None:
        self.added_messages = messages
        self.added_user_id = user_id


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
