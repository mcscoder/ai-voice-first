from datetime import datetime, timedelta, timezone

from app.core.config import MemoryConfig
from app.services.memory.conversation_history import ConversationHistory
from app.services.memory.persistence import MEMORY_PLANNER_TOOL, MemoryAction
from app.services.memory.prompt import (
    build_memory_planner_messages,
    build_response_messages,
)
from app.services.memory.service import MemorySearchResult, MemoryService


class FakeLlm:
    def __init__(self, response: object | list[object]) -> None:
        self.responses = response if isinstance(response, list) else [response]
        self.messages: list[dict[str, str]] | None = None
        self.all_messages: list[list[dict[str, str]]] = []
        self.kwargs: dict[str, object] | None = None
        self.all_kwargs: list[dict[str, object]] = []
        self.client: object | None = None

    def generate_response(self, messages: list[dict[str, str]], **kwargs: object) -> object:
        self.messages = messages
        self.all_messages.append(messages)
        self.kwargs = kwargs
        self.all_kwargs.append(kwargs)
        if len(self.responses) > 1:
            return self.responses.pop(0)
        return self.responses[0]


class FakeMemory:
    def __init__(
        self,
        response: object | list[object],
        memories: list[str] | None = None,
        search_results: list[dict[str, object]] | None = None,
        add_result: dict[str, object] | None = None,
    ) -> None:
        self.llm = FakeLlm(response)
        self.memories = memories or []
        self.search_results = search_results
        self.add_result = add_result
        self.added_messages: object | None = None
        self.added_user_id: str | None = None
        self.added_infer: bool | None = None
        self.updated: list[dict[str, str]] = []
        self.deleted: list[str] = []

    def search(
        self,
        query: str,
        filters: dict[str, str],
        top_k: int,
        threshold: float,
    ) -> dict[str, object]:
        if self.search_results is not None:
            return {"results": self.search_results}
        return {"results": [{"memory": memory} for memory in self.memories]}

    def add(
        self,
        messages: object,
        user_id: str,
        infer: bool = True,
    ) -> dict[str, object] | None:
        self.added_messages = messages
        self.added_user_id = user_id
        self.added_infer = infer
        return self.add_result or {
            "results": [{"id": "added-memory-id", "memory": str(messages), "event": "ADD"}]
        }

    def update(self, memory_id: str, data: str) -> dict[str, str]:
        self.updated.append({"id": memory_id, "memory": data})
        return {"message": "Memory updated successfully!"}

    def delete(self, memory_id: str) -> dict[str, str]:
        self.deleted.append(memory_id)
        return {"message": "Memory deleted successfully!"}


class FakeMemoryService(MemoryService):
    def __init__(
        self,
        memory: FakeMemory,
        memory_config: MemoryConfig | None = None,
    ) -> None:
        self.memory = memory
        self.memory_config = memory_config or MemoryConfig()
        self.history = ConversationHistory()

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


def planner_response(actions: list[dict[str, str]]) -> dict[str, object]:
    return {
        "tool_calls": [
            {
                "name": "plan_memory_actions",
                "arguments": {"actions": actions},
            }
        ]
    }


def test_memory_prompt_requires_plain_spoken_text() -> None:
    memory = FakeMemory("Sure, I can help with that.")
    service = FakeMemoryService(memory)

    service.respond("Can you help me?", "test-user")

    assert memory.llm.all_messages
    system_prompt = memory.llm.all_messages[0][0]["content"]
    assert "plain spoken text only" in system_prompt
    assert "Do not use Markdown" in system_prompt
    assert "real human assistant" in system_prompt


def test_memory_respond_passes_deepseek_thinking_extra_body() -> None:
    memory = FakeMemory("Tôi nghe rồi.")
    service = FakeMemoryService(memory, MemoryConfig(llm_thinking="disabled"))

    service.respond("Xin chào", "test-user")

    assert memory.llm.all_kwargs[0] == {
        "extra_body": {"thinking": {"type": "disabled"}}
    }


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
        [
            """
            ## Here's the plan
            - **Review** your notes
            1. Open `VocalMind`
            > Use [today's list](https://example.com)
            """,
            planner_response(
                [{"event": "ADD", "id": "", "memory": "User should review notes today."}]
            ),
        ],
        memories=["The user reviews notes every morning."],
    )
    service = FakeMemoryService(memory)

    reply = service.respond("What should I do today?", "test-user")

    expected = "Here's the plan Review your notes Open VocalMind Use today's list"
    assert reply.text == expected
    assert memory.added_messages == "User should review notes today."
    assert memory.added_user_id == "test-user"
    assert memory.added_infer is False


def test_memory_respond_injects_previous_completed_turn_into_prompt_and_persist() -> None:
    memory = FakeMemory(
        [
            "Sure.",
            planner_response([{"event": "NONE", "id": "", "memory": ""}]),
            "Sure.",
            planner_response([{"event": "NONE", "id": "", "memory": ""}]),
        ]
    )
    service = FakeMemoryService(memory)

    service.respond("My meeting is at three.", "test-user")
    service.respond("When is it?", "test-user")

    assert memory.llm.all_messages[2][-3:] == [
        {"role": "user", "content": "My meeting is at three."},
        {"role": "assistant", "content": "Sure."},
        {"role": "user", "content": "When is it?"},
    ]
    planner_prompt = memory.llm.all_messages[-1][1]["content"]
    assert "user: My meeting is at three." in planner_prompt
    assert "assistant: Sure." in planner_prompt
    assert "When is it?" in planner_prompt


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

    assert memory.llm.all_messages
    user_prompt = memory.llm.all_messages[0][1]["content"]
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
    memory_csv = user_prompt.split("Relevant memories CSV:\n", maxsplit=1)[1]
    assert "0.82" not in memory_csv
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


def test_build_response_messages_injects_recent_conversation_before_current_query() -> None:
    messages = build_response_messages(
        "What about tomorrow?",
        [],
        [
            {"role": "user", "content": "I have a dentist appointment today."},
            {"role": "assistant", "content": "I will remember that."},
        ],
    )

    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "system"
    assert messages[2] == {
        "role": "user",
        "content": "I have a dentist appointment today.",
    }
    assert messages[3] == {
        "role": "assistant",
        "content": "I will remember that.",
    }
    assert messages[4] == {"role": "user", "content": "What about tomorrow?"}


def test_build_memory_planner_messages_include_recent_context_and_candidates() -> None:
    messages = build_memory_planner_messages(
        "He plays League terribly, so I rage at him.",
        "I understand.",
        [
            {"role": "user", "content": "My friend Minh plays video games badly."},
            {"role": "assistant", "content": "You mean Minh, right?"},
        ],
        [
            MemorySearchResult(
                id="memory-id",
                memory="Có một người chơi Liên Minh rất tệ.",
                score=0.72,
            )
        ],
    )

    assert messages[0]["role"] == "system"
    assert "tiếng Việt" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    prompt = messages[1]["content"]
    assert "user: My friend Minh plays video games badly." in prompt
    assert "assistant: You mean Minh, right?" in prompt
    assert "id=memory-id score=0.72 memory=Có một người chơi Liên Minh rất tệ." in prompt
    assert "He plays League terribly, so I rage at him." in prompt
    assert "ADD" in prompt
    assert "UPDATE" in prompt
    assert "DELETE" in prompt
    assert "NONE" in prompt


def test_memory_planner_tool_schema_is_strict() -> None:
    function = MEMORY_PLANNER_TOOL["function"]
    parameters = function["parameters"]
    action_schema = parameters["properties"]["actions"]["items"]

    assert function["name"] == "plan_memory_actions"
    assert function["strict"] is True
    assert parameters["additionalProperties"] is False
    assert parameters["required"] == ["actions"]
    assert "minItems" not in parameters["properties"]["actions"]
    assert "maxItems" not in parameters["properties"]["actions"]
    assert action_schema["additionalProperties"] is False
    assert action_schema["required"] == ["event", "id", "memory"]
    assert action_schema["properties"]["event"]["enum"] == [
        "ADD",
        "UPDATE",
        "DELETE",
        "NONE",
    ]


def test_memory_planner_uses_forced_tool_call_without_json_response_format() -> None:
    memory = FakeMemory(planner_response([{"event": "NONE", "id": "", "memory": ""}]))
    service = FakeMemoryService(memory, MemoryConfig(llm_thinking="disabled"))

    service.persist_conversation("query", "response", "test-user")

    assert memory.llm.kwargs == {
        "tools": [MEMORY_PLANNER_TOOL],
        "tool_choice": {
            "type": "function",
            "function": {"name": "plan_memory_actions"},
        },
        "extra_body": {"thinking": {"type": "disabled"}},
    }


def test_memory_action_serializes_add_fallback_id() -> None:
    action = MemoryAction(event="ADD", memory="Nguyên nợ tôi năm mươi ngàn.")

    assert action.to_dict() == {
        "id": "",
        "event": "ADD",
        "memory": "Nguyên nợ tôi năm mươi ngàn.",
    }


def test_conversation_history_records_recent_turns_in_order() -> None:
    now = datetime(2026, 6, 26, 9, 0, tzinfo=timezone.utc)
    history = ConversationHistory(now=lambda: now)

    history.record_turn("test-user", "Hello", "Hi.")
    history.record_turn("test-user", "What did I say?", "You said hello.")

    assert history.messages_for("test-user") == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi."},
        {"role": "user", "content": "What did I say?"},
        {"role": "assistant", "content": "You said hello."},
    ]


def test_conversation_history_excludes_messages_older_than_window() -> None:
    current_time = datetime(2026, 6, 26, 9, 0, tzinfo=timezone.utc)
    history = ConversationHistory(
        window=timedelta(minutes=15),
        now=lambda: current_time,
    )

    history.record_turn("test-user", "Old question", "Old answer")
    current_time = current_time + timedelta(minutes=16)
    history.record_turn("test-user", "New question", "New answer")

    assert history.messages_for("test-user") == [
        {"role": "user", "content": "New question"},
        {"role": "assistant", "content": "New answer"},
    ]


def test_conversation_history_isolates_user_ids() -> None:
    history = ConversationHistory()

    history.record_turn("first-user", "First question", "First answer")
    history.record_turn("second-user", "Second question", "Second answer")

    assert history.messages_for("first-user") == [
        {"role": "user", "content": "First question"},
        {"role": "assistant", "content": "First answer"},
    ]
    assert history.messages_for("second-user") == [
        {"role": "user", "content": "Second question"},
        {"role": "assistant", "content": "Second answer"},
    ]


def test_memory_persist_adds_planned_memory_with_add_only_mem0() -> None:
    memory = FakeMemory(
        planner_response(
            [{"event": "ADD", "id": "", "memory": "Nguyên nợ tôi năm mươi ngàn."}]
        )
    )
    service = FakeMemoryService(memory)

    result = service.persist_conversation("query", "response", "test-user")

    assert memory.added_messages == "Nguyên nợ tôi năm mươi ngàn."
    assert memory.added_user_id == "test-user"
    assert memory.added_infer is False
    assert result.actions == [
        MemoryAction(
            event="ADD",
            id="added-memory-id",
            memory="Nguyên nợ tôi năm mươi ngàn.",
        )
    ]
    assert result.action_counts == {"ADD": 1}
    assert result.raw_result is None


def test_memory_persist_updates_ambiguous_candidate_memory() -> None:
    memory = FakeMemory(
        planner_response(
            [
                {
                    "event": "UPDATE",
                    "id": "ambiguous-memory",
                    "memory": (
                        "Bình Nguyên chơi Liên Minh rất tệ và tôi hay chửi Bình Nguyên."
                    ),
                }
            ]
        ),
    )
    service = FakeMemoryService(memory)

    result = service.persist_conversation(
        "thằng đó là cái thằng chơi game rất là ngu và hay bị tôi chửi",
        "Mình hiểu rồi.",
        "test-user",
        [
            {
                "role": "user",
                "content": "Giờ hello bạn biết thằng bạn Bình Nguyên của tôi không",
            },
            {
                "role": "assistant",
                "content": "Tất nhiên là mình biết Bình Nguyên rồi.",
            },
        ],
        [
            MemorySearchResult(
                id="ambiguous-memory",
                memory="Có một người chơi Liên Minh rất tệ và tôi hay chửi người đó",
                score=0.661,
            ),
            MemorySearchResult(
                id="friend-memory",
                memory="Bình Nguyên là bạn của tôi",
                score=0.7,
            ),
        ],
    )

    assert memory.updated == [
        {
            "id": "ambiguous-memory",
            "memory": "Bình Nguyên chơi Liên Minh rất tệ và tôi hay chửi Bình Nguyên.",
        }
    ]
    assert result.actions == [
        MemoryAction(
            event="UPDATE",
            id="ambiguous-memory",
            memory="Bình Nguyên chơi Liên Minh rất tệ và tôi hay chửi Bình Nguyên.",
            previous_memory=(
                "Có một người chơi Liên Minh rất tệ và tôi hay chửi người đó"
            ),
        )
    ]
    assert result.action_counts == {"UPDATE": 1}
    assert memory.llm.all_messages[-1][1]["content"].count("ambiguous-memory") == 1


def test_memory_persist_skips_none_decision() -> None:
    memory = FakeMemory(planner_response([{"event": "NONE", "id": "", "memory": ""}]))
    service = FakeMemoryService(memory)

    result = service.persist_conversation(
        "Tôi muốn nói chuyện khác.",
        "Được thôi.",
        "test-user",
        [],
        [
            MemorySearchResult(
                id="memory-id",
                memory="Có một người chơi Liên Minh rất tệ.",
                score=0.5,
            )
        ],
    )

    assert memory.updated == []
    assert memory.added_messages is None
    assert result.actions == [MemoryAction(event="NONE")]
    assert result.action_counts == {"NONE": 1}


def test_memory_persist_ignores_wrong_planner_tool() -> None:
    memory = FakeMemory(
        {
            "tool_calls": [
                {
                    "name": "wrong_tool",
                    "arguments": {
                        "actions": [
                            {
                                "event": "ADD",
                                "id": "",
                                "memory": "Không được lưu memory này.",
                            }
                        ]
                    },
                }
            ]
        }
    )
    service = FakeMemoryService(memory)

    result = service.persist_conversation("query", "response", "test-user")

    assert memory.added_messages is None
    assert memory.updated == []
    assert memory.deleted == []
    assert result.actions == []
    assert result.action_counts == {}


def test_memory_persist_ignores_invalid_planner_actions() -> None:
    memory = FakeMemory(
        planner_response(
            [
                {"event": "ADD", "id": "", "memory": "   "},
                {
                    "event": "UPDATE",
                    "id": "missing-candidate",
                    "memory": "Không được update memory này.",
                },
                {"event": "DELETE", "id": "missing-candidate", "memory": ""},
                {"event": "UPSERT", "id": "", "memory": "Không được lưu."},
            ]
        )
    )
    service = FakeMemoryService(memory)

    result = service.persist_conversation(
        "query",
        "response",
        "test-user",
        [],
        [
            MemorySearchResult(
                id="candidate-id",
                memory="Candidate memory.",
                score=0.8,
            )
        ],
    )

    assert memory.added_messages is None
    assert memory.updated == []
    assert memory.deleted == []
    assert result.actions == []
    assert result.action_counts == {}


def test_memory_persist_ignores_too_many_planner_actions() -> None:
    memory = FakeMemory(
        planner_response(
            [
                {"event": "ADD", "id": "", "memory": "Memory one."},
                {"event": "ADD", "id": "", "memory": "Memory two."},
                {"event": "ADD", "id": "", "memory": "Memory three."},
                {"event": "ADD", "id": "", "memory": "Memory four."},
            ]
        )
    )
    service = FakeMemoryService(memory)

    result = service.persist_conversation("query", "response", "test-user")

    assert memory.added_messages is None
    assert result.actions == []
    assert result.action_counts == {}


def test_memory_persist_deletes_planned_candidate() -> None:
    memory = FakeMemory(
        planner_response([{"event": "DELETE", "id": "memory-id", "memory": ""}]),
    )
    service = FakeMemoryService(memory)

    result = service.persist_conversation(
        "Xóa chuyện in tài liệu đi.",
        "Được.",
        "test-user",
        [],
        [
            MemorySearchResult(
                id="memory-id",
                memory="Đang dự định in lại tài liệu",
                score=0.8,
            )
        ],
    )

    assert memory.deleted == ["memory-id"]
    assert result.actions == [
        MemoryAction(
            event="DELETE",
            id="memory-id",
            memory="Đang dự định in lại tài liệu",
        )
    ]
    assert result.action_counts == {"DELETE": 1}
