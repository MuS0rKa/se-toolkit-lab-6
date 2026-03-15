# Task 3: The System Agent - Implementation Plan

## 1. New Tool: query_api

- **Purpose:** Allow agent to query the deployed backend API.
- **Parameters:** method (str), path (str), body (str, optional)
- **Authentication:** Uses `LMS_API_KEY` from `.env.docker.secret`.
- **Base URL:** Reads `AGENT_API_BASE_URL` env var (default: `http://localhost:42002`).

## 2. Tool Schema Definition

I will add the following schema to the `TOOLS` list in `agent.py`:

```json
{
    "type": "function",
    "function": {
        "name": "query_api",
        "description": "Make a request to the backend API. Use for live data or API behavior.",
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
