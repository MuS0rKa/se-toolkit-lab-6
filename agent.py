#!/usr/bin/env python3
"""
Agent CLI with tools (read_file, list_files, query_api) and agentic loop.
"""

import os
import sys
import json
import re
import requests
from dotenv import load_dotenv
import argparse
from pathlib import Path

# Load environment variables from both secret files
load_dotenv(".env.agent.secret", override=False)
load_dotenv(".env.docker.secret", override=False)

# Constants
MAX_TOOL_CALLS = 10
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
AGENT_API_BASE_URL = os.getenv("AGENT_API_BASE_URL", "http://localhost:42002")


def debug_log(message):
    """Print debug messages to stderr."""
    print(message, file=sys.stderr)


def validate_path(path):
    """
    Validate and normalize path to prevent directory traversal.
    Returns absolute path if valid, None if invalid.
    """
    try:
        requested_path = os.path.abspath(os.path.join(PROJECT_ROOT, path))
        if not requested_path.startswith(PROJECT_ROOT):
            debug_log(f"Security: Path traversal attempt blocked: {path}")
            return None
        return requested_path
    except Exception as e:
        debug_log(f"Path validation error: {e}")
        return None


def read_file(path):
    """Read contents of a file."""
    valid_path = validate_path(path)
    if not valid_path:
        return f"Error: Invalid path or path traversal detected: {path}"

    try:
        with open(valid_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return f"Error: File not found: {path}"
    except Exception as e:
        return f"Error reading file: {e}"


def list_files(path):
    """List files and directories at given path."""
    valid_path = validate_path(path)
    if not valid_path:
        return f"Error: Invalid path or path traversal detected: {path}"

    try:
        if not os.path.exists(valid_path):
            return f"Error: Path not found: {path}"
        if not os.path.isdir(valid_path):
            return f"Error: Path is not a directory: {path}"

        entries = os.listdir(valid_path)
        return "\n".join(sorted(entries))
    except Exception as e:
        return f"Error listing directory: {e}"


def query_api(method, path, body=None):
    """
    Send an HTTP request to the deployed backend API.
    Returns JSON string with status_code and body.
    """
    api_key = os.getenv("LMS_API_KEY")
    base_url = AGENT_API_BASE_URL.rstrip("/")
    url = base_url + path

    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        kwargs = {"headers": headers, "timeout": 30}
        if body:
            kwargs["data"] = body if isinstance(body, str) else json.dumps(body)

        response = requests.request(method.upper(), url, **kwargs)
        try:
            response_body = response.json()
        except Exception:
            response_body = response.text

        result = {
            "status_code": response.status_code,
            "body": response_body,
        }
        return json.dumps(result)

    except requests.exceptions.ConnectionError as e:
        return json.dumps({"status_code": 0, "body": f"Connection error: {e}"})
    except Exception as e:
        return json.dumps({"status_code": 0, "body": f"Request error: {e}"})


# Tool definitions for function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read the full contents of a file from the project repository. "
                "Use for: wiki documentation, source code files (*.py), "
                "Dockerfile, docker-compose.yml, requirements files. "
                "Always read the relevant source file when asked about code behaviour or bugs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from project root (e.g., 'wiki/git-workflow.md' or 'backend/main.py')",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": (
                "List files and subdirectories at a given path in the project. "
                "Use this to discover what wiki files, source modules, or router files are available. "
                "Router modules are at 'backend/app/routers' (not 'backend/routers'). "
                "Good starting points: 'wiki', 'backend/app', 'backend/app/routers'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative directory path from project root (e.g., 'wiki' or 'backend/routers')",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_api",
            "description": (
                "Send an HTTP request to the deployed backend API and return the response. "
                "Use for: checking live data (item counts, scores), discovering HTTP status codes, "
                "reproducing API errors before reading source code to diagnose bugs. "
                "Always use this tool (not read_file) when the question asks what the API returns, "
                "how many records exist, or what error a specific endpoint produces."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "description": "HTTP method: GET, POST, PUT, DELETE, PATCH",
                    },
                    "path": {
                        "type": "string",
                        "description": "API path including query string if needed (e.g., '/items/' or '/analytics/completion-rate?lab=lab-99')",
                    },
                    "body": {
                        "type": "string",
                        "description": "Optional JSON request body as a string",
                    },
                },
                "required": ["method", "path"],
            },
        },
    },
]

SYSTEM_PROMPT = """You are a software engineering assistant that can inspect a project's wiki, \
source code, and live backend API to answer questions accurately.

PROJECT STRUCTURE (use these exact paths):
- Wiki docs:        wiki/
- Backend source:   backend/app/
- Router modules:   backend/app/routers/
- Main entry point: backend/app/main.py
- Requirements:     backend/requirements.txt

KNOWN ROUTER MODULES in backend/app/routers/:
- items.py        -> handles items (learning content / catalog)
- interactions.py -> handles user interactions with items
- analytics.py    -> handles analytics and statistics
- pipeline.py     -> handles ETL data pipeline
- learners.py     -> handles learner / user management

TOOLS:

1. list_files(path)
   - Use to discover files. For routers: path = "backend/app/routers".
   - For wiki: path = "wiki".

2. read_file(path)
   - Read any file: wiki, Python source, Dockerfile, docker-compose.yml.
   - For bugs: first query_api to reproduce, then read_file to find the line.

3. query_api(method, path, body?)
   - Query the live backend. Use for counts, status codes, live errors.
   - Put query params in the path: e.g. "/analytics/completion-rate?lab=lab-99".

DECISION GUIDE:
- "How many items in the database?" -> query_api GET /items/
- "Status code without auth?" -> query_api GET /items/ without key
- "What framework?" -> read_file backend/app/main.py or backend/requirements.txt
- "List router modules and domains?" -> list_files "backend/app/routers", then answer using the known list above
- "Bug in /analytics/...?" -> query_api first, then read_file the router source

IMPORTANT: always end your answer with:
Source: <path>   (e.g. Source: wiki/github.md  or  Source: backend/app/routers/items.py  or  Source: api)"""


def extract_source(answer: str, all_tool_calls: list) -> str:
    """
    Extract the source reference from the answer or tool calls.
    Priority:
      1. Explicit 'Source: <path>' line in the answer
      2. Any file path found in the answer text
      3. The path argument of the last read_file call
      4. 'api' if query_api was used
      5. Empty string
    """
    # 1. Explicit Source line
    match = re.search(r"[Ss]ource:\s*(\S+)", answer)
    if match:
        return match.group(1)

    # 2. File path pattern in answer text
    match = re.search(r"((?:wiki|backend|plans|tests)/[\w./\-]+\.[\w]+)", answer)
    if match:
        return match.group(1)

    # 3. Last read_file call path
    read_calls = [tc for tc in all_tool_calls if tc["tool"] == "read_file"]
    if read_calls:
        return read_calls[-1]["args"].get("path", "")

    # 4. query_api was used
    api_calls = [tc for tc in all_tool_calls if tc["tool"] == "query_api"]
    if api_calls:
        return "api"

    return ""


def call_llm(messages, tools=None):
    """Call LLM with messages and optional tools."""
    api_key = os.getenv("LLM_API_KEY")
    api_base = os.getenv("LLM_API_BASE")
    model = os.getenv("LLM_MODEL")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    payload = {"model": model, "messages": messages, "temperature": 0.2}

    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    try:
        response = requests.post(
            f"{api_base.rstrip("/")}/chat/completions", headers=headers, json=payload, timeout=60
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        debug_log(f"LLM call failed: {e}")
        raise


def execute_tool_call(tool_call):
    """Execute a tool call and return result."""
    function_name = tool_call["function"]["name"]
    arguments = json.loads(tool_call["function"]["arguments"])

    debug_log(f"Executing {function_name} with args: {arguments}")

    if function_name == "read_file":
        result = read_file(arguments["path"])
    elif function_name == "list_files":
        result = list_files(arguments["path"])
    elif function_name == "query_api":
        result = query_api(
            method=arguments["method"],
            path=arguments["path"],
            body=arguments.get("body"),
        )
    else:
        result = f"Error: Unknown tool {function_name}"

    return {
        "tool_call_id": tool_call["id"],
        "role": "tool",
        "name": function_name,
        "content": result,
    }


def agent_loop(question):
    """Main agentic loop."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    all_tool_calls = []
    tool_call_count = 0

    while tool_call_count < MAX_TOOL_CALLS:
        debug_log(f"\n--- Loop iteration {tool_call_count + 1} ---")

        response = call_llm(messages, TOOLS)
        assistant_message = response["choices"][0]["message"]

        tool_calls = assistant_message.get("tool_calls")

        if not tool_calls:
            # Final answer
            answer = (assistant_message.get("content") or "").strip()
            source = extract_source(answer, all_tool_calls)

            messages.append({"role": "assistant", "content": answer})

            return {
                "answer": answer,
                "source": source,
                "tool_calls": all_tool_calls,
            }

        # Add assistant message with tool calls to history
        messages.append(assistant_message)

        # Execute each tool call
        for tool_call in tool_calls:
            tool_result = execute_tool_call(tool_call)
            messages.append(tool_result)

            all_tool_calls.append(
                {
                    "tool": tool_result["name"],
                    "args": json.loads(tool_call["function"]["arguments"]),
                    "result": tool_result["content"],
                }
            )

            tool_call_count += 1

        if tool_call_count >= MAX_TOOL_CALLS:
            debug_log(f"Reached maximum tool calls ({MAX_TOOL_CALLS})")
            final_response = call_llm(messages)
            answer = (
                final_response["choices"][0]["message"].get("content")
                or "Maximum tool calls reached"
            )
            source = extract_source(answer, all_tool_calls)
            return {"answer": answer, "source": source, "tool_calls": all_tool_calls}

    return {
        "answer": "Maximum iterations reached without final answer",
        "source": "",
        "tool_calls": all_tool_calls,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Ask a question to the documentation and system agent"
    )
    parser.add_argument("question", type=str, help="The question to ask")
    args = parser.parse_args()

    # Validate required LLM environment variables
    if not all(
        [os.getenv("LLM_API_KEY"), os.getenv("LLM_API_BASE"), os.getenv("LLM_MODEL")]
    ):
        debug_log(
            "Error: Missing required LLM environment variables (LLM_API_KEY, LLM_API_BASE, LLM_MODEL)"
        )
        sys.exit(1)

    try:
        result = agent_loop(args.question)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        debug_log(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
