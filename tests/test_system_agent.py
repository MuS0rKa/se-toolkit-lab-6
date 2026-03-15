import subprocess
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_read_file_for_framework():
    """Test that agent uses read_file for framework question."""
    result = subprocess.run(
        [
            sys.executable,
            "agent.py",
            "What Python web framework does this project's backend use?",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    tool_calls = output.get("tool_calls", [])
    assert any(tc.get("tool") == "read_file" for tc in tool_calls), (
        "Expected read_file tool call"
    )


def test_query_api_for_items():
    """Test that agent uses query_api for items count question."""
    result = subprocess.run(
        [sys.executable, "agent.py", "How many items are in the database?"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    tool_calls = output.get("tool_calls", [])
    assert any(tc.get("tool") == "query_api" for tc in tool_calls), (
        "Expected query_api tool call"
    )
