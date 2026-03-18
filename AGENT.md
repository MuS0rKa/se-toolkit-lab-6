# AGENT.md — Project Agent Documentation

## Overview

`agent.py` is a CLI tool that answers questions about the project by combining
three capabilities: reading local files (wiki and source code), listing directory
contents, and querying the live backend API. It uses an LLM with function calling
to decide which tool to invoke and when to stop.

---

## Architecture

```
User (CLI question)
  │
  ▼
agent.py ──► LLM (function calling, max 10 tool calls)
               │
      ┌────────┼────────────┐
      ▼        ▼            ▼
  read_file  list_files  query_api
  (local FS) (local FS)  (HTTP → Backend API)
```

The agentic loop:

1. Send `system prompt + user question + tool definitions` to the LLM.
2. If the LLM returns tool calls, execute them and append results to the message history.
3. Repeat until the LLM returns a plain text answer or 10 tool calls are exhausted.
4. Print the final JSON result to stdout.

---

## Tools

### `read_file(path)`

Reads the full text of any file in the project, identified by a path relative to
the project root. Used for wiki documentation, Python source files, `Dockerfile`,
and `docker-compose.yml`. Includes path traversal protection: requests outside the
project root are rejected.

### `list_files(path)`

Lists all entries (files and subdirectories) in a given directory. Useful for
discovering router modules, wiki pages, or any other files before reading them.

### `query_api(method, path, body?)`

Sends an HTTP request to the deployed backend API.

- **Authentication:** reads `LMS_API_KEY` from the environment and passes it as
  the `X-API-Key` request header.
- **Base URL:** reads `AGENT_API_BASE_URL` from the environment; defaults to
  `http://localhost:42002` if not set.
- **Returns:** a JSON string `{"status_code": <int>, "body": <any>}` so the LLM
  can inspect both the HTTP status and the response body.
- Connection errors are caught and returned as `{"status_code": 0, "body": "..."}`
  rather than crashing.

---

## Environment Variables

| Variable | Purpose | Source |
|---|---|---|
| `LLM_API_KEY` | Authenticates with the LLM provider | `.env.agent.secret` |
| `LLM_API_BASE` | LLM API endpoint (base URL) | `.env.agent.secret` |
| `LLM_MODEL` | Model name to use | `.env.agent.secret` |
| `LMS_API_KEY` | Authenticates with the backend API | `.env.docker.secret` |
| `AGENT_API_BASE_URL` | Backend base URL (optional) | env / defaults to `http://localhost:42002` |

**Important:** no values are hardcoded. The autochecker injects its own values at
evaluation time.

---

## How the LLM Decides Which Tool to Use

The system prompt contains a decision guide:

| Question type | Tool |
|---|---|
| Wiki / documentation | `read_file` on `wiki/` files |
| Source code / framework / architecture | `read_file` on `backend/` files |
| Discover available files or modules | `list_files` |
| Live data (item count, scores) | `query_api` |
| HTTP status codes | `query_api` |
| Bug diagnosis | `query_api` first (reproduce error), then `read_file` (find faulty line) |

Temperature is set to `0.2` to reduce hallucination and keep tool selection consistent.

---

## Lessons Learned from Benchmark

1. **`tool_call.function` access** — the original Task 2 code used attribute access
   (`tool_call.function.name`); some LLM APIs return dicts, so switching to
   `tool_call["function"]["name"]` avoids `AttributeError`.

2. **`content: null` on tool-call turns** — when the LLM makes tool calls it sets
   `content` to `null`. Using `(msg.get("content") or "")` instead of
   `msg.get("content", "")` handles this correctly.

3. **Tool description quality matters** — vague descriptions cause the LLM to pick
   the wrong tool. Explicit "use this for X, not Y" wording in the description
   reduces wrong-tool failures.

4. **Query parameters in path** — for endpoints like `/analytics/completion-rate`,
   query parameters must be included in the `path` argument
   (e.g., `/analytics/completion-rate?lab=lab-99`), not as a separate field.

5. **Temperature** — lowering temperature from `0.7` to `0.2` improved determinism
   for tool-selection decisions.

6. **Both `.env` files** — `LMS_API_KEY` lives in `.env.docker.secret`, not in
   `.env.agent.secret`. Loading both files at startup is required.

7. **Hardcode known structure** — when the project layout is fixed, listing known
   router files and their domains directly in the system prompt prevents the agent
   from spending all 10 tool calls reading individual files and running out before
   it can answer.

---

## Final Eval Score

_9/10 local benchmark (run_eval.py). Question 10 (ETL idempotency) not answered — agent ran out of tool calls before reading the pipeline file._

---

## Running the Agent

```bash
# Single question
uv run agent.py "How many items are in the database?"

# Expected output
{
  "answer": "There are 120 items in the database.",
  "source": "",
  "tool_calls": [
    {"tool": "query_api", "args": {"method": "GET", "path": "/items/"}, "result": "..."}
  ]
}
```
