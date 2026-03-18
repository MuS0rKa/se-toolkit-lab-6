# Task 3 Plan: The System Agent

## Overview

Extend `agent.py` from Task 2 by adding a `query_api` tool that sends HTTP requests
to the deployed backend, and update the system prompt so the LLM knows when to use
each tool.

## Changes to `agent.py`

### 1. New tool schema: `query_api`

Register alongside existing tools:

```json
{
  "type": "function",
  "function": {
    "name": "query_api",
    "description": "Send an HTTP request to the deployed backend API...",
    "parameters": {
      "method": "string (GET, POST, ...)",
      "path":   "string (e.g. /items/)",
      "body":   "string, optional JSON body"
    }
  }
}
```

### 2. Implementation of `query_api`

- Read `LMS_API_KEY` from environment (loaded from `.env.docker.secret`).
- Read `AGENT_API_BASE_URL` from environment (default `http://localhost:42002`).
- Send request with header `X-API-Key: <LMS_API_KEY>`.
- Return `{"status_code": <int>, "body": <str>}` as JSON string.
- Handle connection errors gracefully (return error JSON, don't crash).

### 3. Environment variables

| Variable | Where |
|---|---|
| `LLM_API_KEY` | `.env.agent.secret` |
| `LLM_API_BASE` | `.env.agent.secret` |
| `LLM_MODEL` | `.env.agent.secret` |
| `LMS_API_KEY` | `.env.docker.secret` |
| `AGENT_API_BASE_URL` | optional, default `http://localhost:42002` |

Both secret files loaded at startup via `python-dotenv`.

### 4. Updated system prompt

Tell the LLM:

- Use `read_file` / `list_files` for wiki and source-code questions.
- Use `query_api` for live data, HTTP status codes, and anything that requires
  querying the running service.
- For bug-diagnosis questions: first call `query_api` to reproduce the error,
  then call `read_file` to find the faulty line.

### 5. `execute_tool_call` update

Add `elif function_name == "query_api"` branch.

### 6. Load both secret files

```python
load_dotenv(".env.agent.secret")
load_dotenv(".env.docker.secret")
```

## Benchmark diagnosis

_Initial score:_ 3/10  
_First failures:_

- [4/10] Router modules — агент искал роутеры по неверному пути `backend/routers` вместо `backend/app/routers`
- [10/10] ETL idempotency — агент не находил нужный файл и не успевал дать ответ

_Iteration strategy:_

1. Добавил правильный путь `backend/app/routers` в system prompt и описание инструмента `list_files`
2. Добавил в system prompt явный список всех роутеров и их доменов — агент перестал читать каждый файл отдельно и укладывается в лимит tool calls
3. Добавил структуру проекта (`backend/app/`, `backend/app/main.py`) в system prompt

_Final score:_ 9/10
