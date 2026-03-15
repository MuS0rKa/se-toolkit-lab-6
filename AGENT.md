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
