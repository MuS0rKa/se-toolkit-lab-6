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
