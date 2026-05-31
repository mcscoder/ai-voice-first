# Memory RAG Under The Hood

## Overview

The assistant memory path is now retrieval-augmented generation. It does not load
the newest memories first. For each voice request, the backend uses the current
transcript as a query, retrieves relevant stored facts from SQLite, formats a
small memory context, then sends that context to the assistant as reference data.

Default mode is local SQLite RAG with structured and lexical retrieval. Semantic
embedding retrieval is optional and disabled unless configured.

## Request Flow

```text
voice audio
  -> transcription
  -> transcript text
  -> memory retrieval query
  -> compact memory context
  -> assistant completion
  -> text-to-speech
  -> response audio
```

The route entry point is `backend/assistant_routes.py`.

For a normal request:

1. Audio is transcribed.
2. The transcript is passed to `MemoryService.build_context("local-user", transcript)`.
3. `MemoryRetrievalService.search()` finds relevant memories.
4. `MemoryContextBuilder` formats the selected results.
5. `VoiceAssistantService.build_payload()` sends:
   - system prompt
   - memory safety instruction
   - untrusted memory context as a separate user message
   - the real user transcript as the final user message
6. After the response, the transcript may be stored as a new memory if it is not
   a pure recall question.

## Retrieval Layers

The retrieval service combines three candidate sources.

### 1. Structured Finance And Person Retrieval

This is the strongest path for questions like:

```text
ai nợ tao tiền?
Minh nợ bao nhiêu?
```

The loader checks:

- whether the query looks financial, using terms such as `nợ`, `tiền`, `debt`,
  `owe`, `owed`
- whether the query mentions a known person name or alias
- open debt records only: `financial_records.type = 'debt_owed'` and
  `status = 'pending'`

This avoids answering debt questions from unrelated rows such as expenses,
settled debts, or money the user owes someone else.

### 2. Lexical Retrieval

Lexical retrieval scans a bounded number of memory rows and scores exact token
overlap between query tokens and memory text/category/person.

Example:

```text
query: "Minh nợ bao nhiêu?"
tokens: {"minh", "nợ", "bao", "nhiêu"}
```

Rows that share meaningful tokens score higher. Category hints can add score,
for example finance-like terms matching finance memories.

For finance queries, lexical retrieval is restricted to open debt rows, so a
short token such as `ai` does not pull unrelated memories like `mai gặp Minh`.

### 3. Optional Semantic Embedding Retrieval

Embedding retrieval is disabled by default.

Enable it with:

```text
MEMORY_EMBEDDINGS_ENABLED=true
MEMORY_EMBEDDING_API_BASE_URL=http://...
MEMORY_EMBEDDING_MODEL=text-embedding-3-small
```

When enabled:

1. New memories get embeddings after the memory row is committed.
2. Retrieval embeds the current query.
3. Stored vectors in `memory_embeddings` are compared with cosine similarity.
4. Similar rows above the threshold are added as candidates.

If embedding generation fails, the assistant continues with structured and
lexical retrieval.

## Ranking

All candidate sources merge into one result map by `memory_id`.

If the same memory appears from multiple paths, the highest score wins.

Then results are filtered and sorted by:

1. retrieval score
2. memory importance
3. recency

Only the top results are sent into the assistant context.

## Context Formatting

`MemoryContextBuilder` formats retrieved memories like this:

```text
[MEMORY CONTEXT]
- Minh owes user 500000 VND (finance, 2026-05-31T...) [person=Minh, amount=500000 VND, status=pending]
[/MEMORY CONTEXT]
```

The context has a character budget, currently 1600 characters, so retrieval
cannot dump the whole memory database into the prompt.

## Prompt Safety

Stored memory is treated as untrusted user data.

The assistant system prompt receives an instruction saying memory context is
reference data only. The actual memory text is sent as a separate user message
wrapped in `[MEMORY CONTEXT]` markers. This reduces the chance that stored text
can act like system instructions.

Prompt logs default to `assistant_prompt.log`. Memory context and extraction
payloads are redacted before they are written.

## Memory Storage Gate

The backend stores factual statements but skips pure recall questions.

Stored:

```text
mai gặp Minh
Minh nợ tao 500k
```

Skipped:

```text
ai nợ tao tiền?
Minh nợ bao nhiêu?
lần cuối gặp Minh khi nào?
```

This prevents user questions from becoming fake facts in future retrieval.

## Runtime Controls

Key environment variables:

| Variable | Meaning |
| --- | --- |
| `ASSISTANT_USE_MEMORY_CONTEXT` | Enable retrieval before assistant completion. |
| `ASSISTANT_STORE_MEMORIES` | Enable storing transcripts after assistant response. |
| `ASSISTANT_ALLOW_REMOTE_MEMORY_CONTEXT` | Allow non-loopback requests to use memory. Default is true. |
| `ASSISTANT_PROMPT_LOG_FILE` | Prompt log file path. Default is `assistant_prompt.log`. |
| `MEMORY_RAG_MAX_CANDIDATES` | Maximum rows scanned per retrieval path. Default is 300. |
| `MEMORY_EMBEDDINGS_ENABLED` | Enable optional semantic retrieval. Default is false. |
| `MEMORY_EMBEDDING_API_BASE_URL` | OpenAI-compatible embeddings endpoint. |
| `MEMORY_EMBEDDING_MODEL` | Embedding model name. |

## Current Limitations

- Memory identity is still hardcoded as `local-user`.
- Set `ASSISTANT_ALLOW_REMOTE_MEMORY_CONTEXT=false` if memory should only work
  from loopback clients.
- Semantic retrieval only works after embeddings are enabled and new memories
  have vectors.
- Reminders, long-term insights, and command routing are outside this RAG layer.

## Code Map

| Concern | File |
| --- | --- |
| Voice route and memory call | `backend/assistant_routes.py` |
| Public memory service API | `backend/memory/memory_service.py` |
| Retrieval orchestration | `backend/memory/retrieval_service.py` |
| Candidate SQL and scoring | `backend/memory/retrieval_candidate_loader.py` |
| Context formatting | `backend/memory/context_builder.py` |
| Optional embeddings | `backend/memory/embedding_service.py` |
| Recall-question storage gate | `backend/memory/intent.py` |
| Assistant payload and prompt framing | `backend/assistant_service.py` |
