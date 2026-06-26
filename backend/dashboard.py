from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components


def dashboard_component(base_url: str, access_token: str) -> str:
    base_url_literal = json.dumps(base_url.rstrip("/"))
    access_token_literal = json.dumps(access_token.strip())
    template = """
<div id="app" class="dashboard">
  <div class="topbar">
    <div>
      <h2>VocalMind Voice Assistant Pipeline</h2>
      <p>Live view of ASR, memory retrieval, LLM streaming, TTS chunks, and Mem0 persistence.</p>
    </div>
    <div id="connection" class="connection pending">Connecting...</div>
  </div>

  <div id="services" class="services"></div>
  <h3>Live Pipeline</h3>
  <div id="pipeline" class="pipeline"></div>
  <div id="details" class="details"></div>
  <div id="memory-panels" class="memory-grid"></div>
  <h3>Recent Runs</h3>
  <div id="recent" class="recent"></div>
</div>

<style>
  :root {
    --border: #d1d5db;
    --muted: #6b7280;
    --text: #111827;
    --panel: #ffffff;
    --page: #f8fafc;
  }

  * {
    box-sizing: border-box;
    min-width: 0;
  }

  html,
  body {
    margin: 0;
    background: var(--page);
    color: var(--text);
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    overflow-x: hidden;
  }

  .dashboard {
    width: 100%;
    max-width: 100%;
    padding: 12px 10px 28px;
    overflow-x: hidden;
  }

  .topbar {
    display: flex;
    align-items: start;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 18px;
  }

  h2, h3 {
    margin: 0;
    letter-spacing: 0;
  }

  h2 {
    font-size: 24px;
  }

  h3 {
    font-size: 18px;
    margin-top: 18px;
    margin-bottom: 10px;
  }

  p {
    margin: 6px 0 0;
    color: var(--muted);
  }

  .connection {
    border-radius: 999px;
    padding: 6px 12px;
    font-size: 13px;
    font-weight: 700;
    white-space: nowrap;
  }

  .connection.pending {
    background: #fef3c7;
    color: #78350f;
  }

  .connection.open {
    background: #d1fae5;
    color: #064e3b;
  }

  .connection.error {
    background: #fee2e2;
    color: #7f1d1d;
  }

  .services {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 12px;
  }

  .service-card,
  .stage-card,
  .detail-card {
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--panel);
    padding: 12px;
  }

  .service-label,
  .stage-status,
  .detail-label {
    color: var(--muted);
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
  }

  .service-value {
    margin-top: 6px;
    font-weight: 750;
    overflow-wrap: anywhere;
  }

  .pipeline {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 12px;
  }

  .stage-card {
    min-height: 112px;
    border-left: 8px solid #e5e7eb;
  }

  .stage-card.running {
    border-left-color: #f59e0b;
  }

  .stage-card.done {
    border-left-color: #10b981;
  }

  .stage-card.error {
    border-left-color: #ef4444;
  }

  .stage-card.cancelled {
    border-left-color: #6b7280;
  }

  .stage-card.skipped {
    border-left-color: #9ca3af;
  }

  .stage-label {
    margin-top: 6px;
    font-size: 15px;
    font-weight: 760;
  }

  .stage-duration {
    margin-top: 8px;
    color: #374151;
  }

  .pill {
    display: inline-block;
    margin-top: 8px;
    border-radius: 999px;
    padding: 2px 8px;
    background: #e5e7eb;
    color: #374151;
    font-size: 12px;
    max-width: 100%;
    overflow-wrap: anywhere;
  }

  .stage-card.running .pill {
    background: #f59e0b;
    color: #111827;
  }

  .stage-card.done .pill {
    background: #10b981;
    color: #052e1a;
  }

  .stage-card.error .pill {
    background: #ef4444;
    color: #ffffff;
  }

  .stage-card.cancelled .pill,
  .stage-card.skipped .pill {
    background: #e5e7eb;
    color: #374151;
  }

  .details {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 12px;
    margin-top: 14px;
  }

  .memory-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
    gap: 12px;
    margin-top: 12px;
  }

  .detail-value {
    margin-top: 8px;
    min-height: 58px;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
  }

  .metrics {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
    margin-top: 8px;
  }

  .metric {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 10px;
  }

  .metric div:first-child {
    color: var(--muted);
    font-size: 12px;
  }

  .metric div:last-child {
    margin-top: 4px;
    font-size: 20px;
    font-weight: 780;
  }

  .memory-list,
  .action-list,
  .prompt-list,
  .chunk-list,
  .tts-chunk-list {
    display: grid;
    gap: 8px;
    margin-top: 10px;
    max-height: 420px;
    overflow-y: auto;
    overflow-x: hidden;
  }

  .memory-item,
  .action-item,
  .prompt-item,
  .chunk-item,
  .tts-chunk-item {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 10px;
    background: #f9fafb;
    overflow-wrap: anywhere;
  }

  .memory-item-header {
    display: flex;
    align-items: start;
    justify-content: space-between;
    gap: 10px;
  }

  .chunk-header {
    display: flex;
    align-items: start;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 6px;
  }

  .chunk-index,
  .chunk-status {
    flex: 0 0 auto;
    border-radius: 999px;
    padding: 2px 8px;
    font-size: 12px;
    font-weight: 800;
    white-space: nowrap;
  }

  .chunk-index {
    background: #eef2ff;
    color: #3730a3;
  }

  .chunk-status {
    background: #e5e7eb;
    color: #374151;
  }

  .chunk-status.queued {
    background: #fef3c7;
    color: #78350f;
  }

  .chunk-status.synthesizing {
    background: #fed7aa;
    color: #7c2d12;
  }

  .chunk-status.synthesized {
    background: #dbeafe;
    color: #1e3a8a;
  }

  .chunk-status.streamed {
    background: #d1fae5;
    color: #064e3b;
  }

  .current-chunk {
    margin-top: 8px;
    border: 1px solid #fed7aa;
    border-radius: 8px;
    padding: 10px;
    background: #fff7ed;
    overflow-wrap: anywhere;
  }

  .score-badge {
    flex: 0 0 auto;
    border-radius: 999px;
    padding: 2px 8px;
    background: #eef2ff;
    color: #3730a3;
    font-size: 12px;
    font-weight: 800;
    white-space: nowrap;
  }

  .memory-meta {
    margin-top: 8px;
    color: #6b7280;
    font-size: 12px;
    line-height: 1.5;
  }

  .memory-field {
    display: grid;
    grid-template-columns: 110px minmax(0, 1fr);
    gap: 8px;
    margin-top: 5px;
  }

  .memory-field span:first-child,
  .prompt-role {
    color: #374151;
    font-weight: 800;
  }

  .prompt-content {
    margin: 8px 0 0;
    color: #111827;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
    font-size: 12px;
    line-height: 1.5;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
  }

  .action-header {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr);
    gap: 8px;
    margin-bottom: 6px;
    overflow-wrap: anywhere;
  }

  .action-header span:last-child {
    text-align: right;
    overflow-wrap: anywhere;
  }

  .event-badge {
    border-radius: 999px;
    padding: 2px 8px;
    font-size: 12px;
    font-weight: 800;
  }

  .event-badge.ADD {
    background: #d1fae5;
    color: #064e3b;
  }

  .event-badge.UPDATE {
    background: #dbeafe;
    color: #1e3a8a;
  }

  .event-badge.DELETE {
    background: #fee2e2;
    color: #7f1d1d;
  }

  .event-badge.NONE {
    background: #e5e7eb;
    color: #374151;
  }

  .previous-memory {
    color: #6b7280;
    font-size: 13px;
    margin-bottom: 5px;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    background: #ffffff;
    border: 1px solid var(--border);
    border-radius: 8px;
    table-layout: fixed;
    overflow-wrap: anywhere;
  }

  .recent {
    overflow-x: hidden;
  }

  th, td {
    border-bottom: 1px solid #e5e7eb;
    padding: 9px 10px;
    text-align: left;
    font-size: 13px;
  }

  th {
    color: #374151;
    background: #f3f4f6;
  }

  tr:last-child td {
    border-bottom: 0;
  }

  .empty {
    border: 1px dashed var(--border);
    border-radius: 8px;
    padding: 18px;
    background: #ffffff;
    color: var(--muted);
  }

  @media (max-width: 1100px) {
    .details,
    .memory-grid {
      grid-template-columns: 1fr;
    }
  }

  @media (max-width: 760px) {
    .details,
    .memory-grid {
      grid-template-columns: 1fr;
    }
  }
</style>

<script>
  const baseUrl = __BASE_URL__;
  const accessToken = __ACCESS_TOKEN__;
  const stageNames = [
    "request_received",
    "asr",
    "memory_search",
    "llm_response_stream",
    "tts_synthesis",
    "client_stream_done",
    "mem0_persist_background",
  ];

  const serviceLabels = [
    ["ASR", "asr_model"],
    ["LLM", "llm_model"],
    ["Memory", "embedder_model"],
    ["TTS voice", "tts_voice"],
  ];

    let abortController = null;

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function formatMs(value) {
    if (typeof value !== "number") {
      return "-";
    }
    if (value >= 1000) {
      return `${(value / 1000).toFixed(2)}s`;
    }
    return `${Math.round(value)}ms`;
  }

  function stageByName(run, name) {
    return (run?.stages || []).find((stage) => stage.name === name) || {
      name,
      label: name,
      status: "pending",
      duration_ms: null,
      metadata: {},
    };
  }

  function stageDetail(stage) {
    const metadata = stage.metadata || {};
    if ("memory_count" in metadata) {
      return `${metadata.memory_count} memories`;
    }
    if ("characters" in metadata) {
      return `${metadata.characters} chars`;
    }
    if ("chunk_count" in metadata) {
      if (metadata.current_chunk) {
        return `TTS #${metadata.current_chunk.sequence} synthesizing`;
      }
      return `${metadata.chunk_count} audio chunks`;
    }
    if ("persisted" in metadata) {
      if (metadata.persisted === false) {
        return `Skipped: ${metadata.skip_reason || "not persisted"}`;
      }
      const counts = metadata.action_counts || {};
      const total = Object.values(counts).reduce((sum, count) => sum + Number(count || 0), 0);
      return `${total} memory actions`;
    }
    return stage.name;
  }

  function formatFieldValue(value) {
    if (typeof value === "object" && value !== null) {
      return JSON.stringify(value);
    }
    return value ?? "";
  }

  function renderSearchedMemories(memory) {
    const memories = memory.memories || [];
    if (memories.length === 0) {
      return '<div class="empty">No relevant memories found for this query.</div>';
    }

    return `
      <div class="memory-list">
        ${memories.map((item) => {
          const memoryText = typeof item === "string" ? item : item.memory;
          const score = typeof item === "object" && item !== null ? item.score : null;
          const scoreText = typeof score === "number" ? score.toFixed(3) : "-";
          let fieldRows = "";
          if (typeof item === "object" && item !== null) {
            fieldRows = Object.entries(item)
              .filter(([key]) => key !== "memory" && key !== "score")
              .map(([key, value]) => `
                <div class="memory-field">
                  <span>${escapeHtml(key)}</span>
                  <span>${escapeHtml(formatFieldValue(value))}</span>
                </div>
              `)
              .join("");
          }
          return `
            <div class="memory-item">
              <div class="memory-item-header">
                <div>${escapeHtml(memoryText)}</div>
                <span class="score-badge">score ${escapeHtml(scoreText)}</span>
              </div>
              ${fieldRows ? `<div class="memory-meta">${fieldRows}</div>` : ""}
            </div>
          `;
        }).join("")}
      </div>
    `;
  }

  function renderPromptMessages(llm) {
    const messages = llm.prompt_messages || [];
    if (messages.length === 0) {
      return '<div class="empty">Waiting for built LLM prompt...</div>';
    }

    return `
      <div class="prompt-list">
        ${messages.map((message) => `
          <div class="prompt-item">
            <div class="prompt-role">${escapeHtml(message.role || "unknown")}</div>
            <pre class="prompt-content">${escapeHtml(message.content || "")}</pre>
          </div>
        `).join("")}
      </div>
    `;
  }

  function renderReplyChunks(llm) {
    const chunks = llm.reply_chunks || [];
    if (chunks.length === 0) {
      return '<div class="empty">Waiting for LLM stream chunks...</div>';
    }

    return `
      <div class="chunk-list">
        ${chunks.map((chunk) => `
          <div class="chunk-item">
            <div class="chunk-header">
              <span class="chunk-index">#${escapeHtml(chunk.index ?? "-")}</span>
            </div>
            <div>${escapeHtml(chunk.text || "")}</div>
          </div>
        `).join("")}
      </div>
    `;
  }

  function renderTtsChunks(tts) {
    const chunks = tts.chunks || [];
    const current = tts.current_chunk;
    const currentMarkup = current
      ? `
        <div class="current-chunk">
          <div class="detail-label">Currently synthesizing</div>
          <div>#${escapeHtml(current.sequence)} · ${escapeHtml(current.text || "")}</div>
        </div>
      `
      : '<div class="empty">No TTS chunk is currently synthesizing.</div>';

    if (chunks.length === 0) {
      return `${currentMarkup}<div class="empty">Waiting for TTS chunks...</div>`;
    }

    return `
      ${currentMarkup}
      <div class="tts-chunk-list">
        ${chunks.map((chunk) => {
          const status = chunk.status || "unknown";
          const duration = typeof chunk.duration_ms === "number" ? formatMs(chunk.duration_ms) : "-";
          return `
            <div class="tts-chunk-item">
              <div class="chunk-header">
                <span class="chunk-index">#${escapeHtml(chunk.sequence ?? "-")}</span>
                <span class="chunk-status ${escapeHtml(status)}">${escapeHtml(status)} · ${escapeHtml(duration)}</span>
              </div>
              <div>${escapeHtml(chunk.text || "")}</div>
            </div>
          `;
        }).join("")}
      </div>
    `;
  }

  function renderMemoryActions(persist) {
    const actions = persist.memory_actions || [];
    const counts = persist.action_counts || {};
    const countText = ["ADD", "UPDATE", "DELETE", "NONE"]
      .filter((event) => counts[event])
      .map((event) => `${event}: ${counts[event]}`)
      .join(" · ");

    if (actions.length === 0) {
      return `
        <div class="empty">
          ${persist.persisted
            ? "Mem0 persisted the conversation, but no memory action was returned."
            : persist.skip_reason
              ? `Mem0 persistence skipped: ${escapeHtml(persist.skip_reason)}`
              : "Waiting for Mem0 persistence..."}
        </div>
      `;
    }

    return `
      <div class="detail-value">${escapeHtml(countText || `${actions.length} actions`)}</div>
      <div class="action-list">
        ${actions.map((action) => {
          const event = action.event || "UNKNOWN";
          const memory = action.memory || "";
          const previous = action.previous_memory;
          return `
            <div class="action-item">
              <div class="action-header">
                <span class="event-badge ${escapeHtml(event)}">${escapeHtml(event)}</span>
                <span>${escapeHtml(action.id || "")}</span>
              </div>
              ${previous ? `<div class="previous-memory">Old: ${escapeHtml(previous)}</div>` : ""}
              <div>${event === "NONE" ? "No change: " : ""}${escapeHtml(memory)}</div>
            </div>
          `;
        }).join("")}
      </div>
    `;
  }

  function setConnection(className, text) {
    const element = document.getElementById("connection");
    element.className = `connection ${className}`;
    element.textContent = text;
  }

  function renderServices(services) {
    document.getElementById("services").innerHTML = serviceLabels
      .map(([label, key]) => `
        <div class="service-card">
          <div class="service-label">${escapeHtml(label)}</div>
          <div class="service-value">${escapeHtml(services?.[key] || "-")}</div>
        </div>
      `)
      .join("");
  }

  function renderPipeline(run) {
    if (!run) {
      document.getElementById("pipeline").innerHTML = `
        <div class="empty" style="grid-column: 1 / -1;">
          Send a voice request to /v1/voice/assistant/stream to populate the dashboard.
        </div>
      `;
      return;
    }

    document.getElementById("pipeline").innerHTML = stageNames
      .map((name) => {
        const stage = stageByName(run, name);
        const status = stage.status || "pending";
        return `
          <div class="stage-card ${escapeHtml(status)}">
            <div class="stage-status">${escapeHtml(status).toUpperCase()}</div>
            <div class="stage-label">${escapeHtml(stage.label || stage.name)}</div>
            <div class="stage-duration">${formatMs(stage.duration_ms)}</div>
            <div class="pill">${escapeHtml(stageDetail(stage))}</div>
          </div>
        `;
      })
      .join("");
  }

  function renderDetails(run) {
    if (!run) {
      document.getElementById("details").innerHTML = "";
      document.getElementById("memory-panels").innerHTML = "";
      return;
    }

    const asr = stageByName(run, "asr").metadata || {};
    const memory = stageByName(run, "memory_search").metadata || {};
    const llm = stageByName(run, "llm_response_stream").metadata || {};
    const tts = stageByName(run, "tts_synthesis").metadata || {};
    const persist = stageByName(run, "mem0_persist_background").metadata || {};

    document.getElementById("details").innerHTML = `
      <div class="detail-card">
        <div class="detail-label">Transcript</div>
        <div class="detail-value">${escapeHtml(asr.transcript || "Waiting for ASR...")}</div>
      </div>
      <div class="detail-card">
        <div class="detail-label">Assistant reply chunks</div>
        ${renderReplyChunks(llm)}
      </div>
      <div class="detail-card">
        <div class="detail-label">TTS chunk status</div>
        ${renderTtsChunks(tts)}
      </div>
      <div class="detail-card">
        <div class="detail-label">Run details</div>
        <div class="metrics">
          <div class="metric"><div>Status</div><div>${escapeHtml(run.status || "-")}</div></div>
          <div class="metric"><div>Total</div><div>${formatMs(run.total_duration_ms)}</div></div>
          <div class="metric"><div>Stage</div><div>${escapeHtml(run.current_stage || "-")}</div></div>
          <div class="metric"><div>Memories</div><div>${escapeHtml(memory.memory_count ?? 0)}</div></div>
          <div class="metric"><div>LLM chars</div><div>${escapeHtml(llm.characters ?? 0)}</div></div>
          <div class="metric"><div>TTS chunks</div><div>${escapeHtml(tts.chunk_count ?? 0)}</div></div>
        </div>
      </div>
    `;

    document.getElementById("memory-panels").innerHTML = `
      <div class="detail-card">
        <div class="detail-label">Retrieved Memory Context</div>
        ${renderSearchedMemories(memory)}
      </div>
      <div class="detail-card">
        <div class="detail-label">Built LLM Prompt</div>
        ${renderPromptMessages(llm)}
      </div>
      <div class="detail-card">
        <div class="detail-label">Mem0 Persistence Actions</div>
        ${renderMemoryActions(persist)}
      </div>
    `;
  }

  function renderRecent(runs) {
    if (!runs || runs.length === 0) {
      document.getElementById("recent").innerHTML = '<div class="empty">No completed assistant stream runs yet.</div>';
      return;
    }

    const rows = runs.map((run) => `
      <tr>
        <td>${escapeHtml(run.run_id)}</td>
        <td>${escapeHtml(run.status)}</td>
        <td>${formatMs(run.total_duration_ms)}</td>
        <td>${formatMs(stageByName(run, "asr").duration_ms)}</td>
        <td>${formatMs(stageByName(run, "memory_search").duration_ms)}</td>
        <td>${formatMs(stageByName(run, "llm_response_stream").duration_ms)}</td>
        <td>${formatMs(stageByName(run, "tts_synthesis").duration_ms)}</td>
        <td>${formatMs(stageByName(run, "mem0_persist_background").duration_ms)}</td>
      </tr>
    `).join("");

    document.getElementById("recent").innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Run</th>
            <th>Status</th>
            <th>Total</th>
            <th>ASR</th>
            <th>Memory</th>
            <th>LLM</th>
            <th>TTS</th>
            <th>Persist</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    `;
  }

  function render(payload) {
    renderServices(payload.services || {});
    const activeRuns = payload.active_runs || [];
    const recentRuns = payload.recent_runs || [];
    const run = activeRuns[0] || recentRuns[0] || null;
    renderPipeline(run);
    renderDetails(run);
    renderRecent(recentRuns);
  }

  function handleSseBlock(block) {
    const lines = block.split("\\n");
    let eventName = "";
    const dataLines = [];
    for (const line of lines) {
      if (line.startsWith("event:")) {
        eventName = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).trimStart());
      }
    }
    if (eventName !== "telemetry" || dataLines.length === 0) {
      return;
    }
    setConnection("open", "Live SSE connected");
    render(JSON.parse(dataLines.join("\\n")));
  }

  async function connect() {
    if (!baseUrl) {
      setConnection("error", "Missing backend URL");
      return;
    }
    const streamUrl = `${baseUrl}/v1/voice/assistant/telemetry/stream`;
    const headers = accessToken ? { Authorization: `Bearer ${accessToken}` } : {};
    abortController = new AbortController();
    try {
      const response = await fetch(streamUrl, {
        headers,
        signal: abortController.signal,
      });
      if (!response.ok || !response.body) {
        if (response.status === 401) {
          setConnection("error", "Auth required: enable public telemetry or provide a token");
          return;
        }
        setConnection("error", `SSE failed (${response.status})`);
        return;
      }

      setConnection("open", "Live SSE connected");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          break;
        }
        buffer += decoder.decode(value, { stream: true });
        const blocks = buffer.split("\\n\\n");
        buffer = blocks.pop() || "";
        for (const block of blocks) {
          handleSseBlock(block);
        }
      }
      setConnection("error", "SSE disconnected");
    } catch (error) {
      setConnection("error", "SSE disconnected");
    }
  }

  connect();
</script>
"""
    return template.replace("__BASE_URL__", base_url_literal).replace(
        "__ACCESS_TOKEN__",
        access_token_literal,
    )


def main() -> None:
    st.set_page_config(
        page_title="VocalMind Pipeline Dashboard",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(
        """
        <style>
          header[data-testid="stHeader"],
          div[data-testid="stToolbar"],
          #MainMenu,
          footer {
            display: none !important;
          }
          .block-container {
            max-width: 100% !important;
            padding: 0 !important;
          }
          iframe {
            width: 100% !important;
            border: 0 !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    access_token = st.sidebar.text_input("Access token", type="password")
    components.html(
        dashboard_component("http://theunseenblade.ddns.net:8000", access_token),
        height=1800,
        scrolling=True,
    )


if __name__ == "__main__":
    main()
