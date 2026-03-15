# Agent Documentation

## Overview

This agent is a simple CLI program that connects to a Large Language Model (LLM) and answers questions. It serves as the foundation for more complex agents that will be built in subsequent tasks.

## Architecture

### Components

1. **Configuration Loader** — reads API credentials from `.env.agent.secret`
2. **Input Parser** — extracts question from command-line arguments
3. **API Client** — sends HTTP requests to the LLM endpoint
4. **Response Parser** — extracts the answer from the LLM response
5. **Output Formatter** — formats the result as JSON

### Data Flow

```mermaid
flowchart LR
    User[User] -->|Question via CLI| Agent[agent.py]
    Agent -->|Reads| Env[.env.agent.secret]
    Agent -->|POST /v1/chat/completions| Proxy[Qwen API Proxy on VM]
    Proxy -->|Forwards request| Qwen[Qwen Cloud LLM]
    Qwen -->|Response| Proxy
    Proxy -->|Response| Agent
    Agent -->|JSON stdout| User


## Tools

The agent now has two tools for accessing documentation:

### 1. list_files
- **Description**: Lists files and directories at a given path
- **Parameters**: `path` (string) - relative path from project root
- **Security**: Prevents directory traversal attacks
- **Use**: First tool to call to discover available wiki files

### 2. read_file
- **Description**: Reads contents of a file
- **Parameters**: `path` (string) - relative path from project root
- **Security**: Validates path to stay within project root
- **Use**: Read wiki files to find answers

## Agentic Loop

The agent follows this loop:
1. Send question + tool definitions to LLM
2. If LLM requests tools → execute them, append results, repeat (max 10 times)
3. If LLM responds with text → that's the final answer
4. Output JSON with answer, source, and all tool_calls

## System Prompt
The system prompt instructs the LLM to:
- Use list_files first to discover wiki contents
- Then read_file to examine relevant files
- Include source references
- Stop when answer is found

## Output Format
```json
{
  "answer": "Edit the conflicting file, choose which changes to keep, then stage and commit.",
  "source": "wiki/git-workflow.md#resolving-merge-conflicts",
  "tool_calls": [
    {"tool": "list_files", "args": {"path": "wiki"}, "result": "git-workflow.md\n..."},
    {"tool": "read_file", "args": {"path": "wiki/git-workflow.md"}, "result": "..."}
  ]
}

## Task 3: System Agent Implementation

### Overview
For Task 3, I extended the documentation agent from Task 2 with system-level capabilities by adding a `query_api` tool. This allows the agent to interact with the live backend service, enabling it to answer questions about real-time data and API behavior.

### New Tool: `query_api`
The `query_api` tool is a function-calling interface to the deployed backend API. It accepts three parameters:
- `method`: HTTP method (GET, POST)
- `path`: API endpoint path (e.g., `/items/`, `/analytics/completion-rate?lab=lab-99`)
- `body`: Optional JSON request body for POST requests

The tool authenticates using the `LMS_API_KEY` from `.env.docker.secret` and sends requests to the base URL specified in `AGENT_API_BASE_URL` (defaults to `http://localhost:42002`). The response is returned as a JSON string containing `status_code` and `body`.

### Tool Schema
The tool is registered with the LLM using the following schema:
```json
{
    "type": "function",
    "function": {
        "name": "query_api",
        "description": "Make a request to the backend API. Use this for questions about live data (item count, scores, status codes).",
        "parameters": {
            "type": "object",
            "properties": {
                "method": {"type": "string", "enum": ["GET", "POST"]},
                "path": {"type": "string"},
                "body": {"type": "string"}
            },
            "required": ["method", "path"]
        }
    }
}
