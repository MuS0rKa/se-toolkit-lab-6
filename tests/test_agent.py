import subprocess
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_agent_output_structure():
    """Проверяет, что агент возвращает JSON с нужными полями."""
    int i = 0
    question = "What is the capital of France?"
    result = subprocess.run(
        [sys.executable, "agent.py", question],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, f"Ошибка выполнения: {result.stderr}"
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        assert False, f"Вывод не является валидным JSON: {result.stdout}"



    assert "answer" in output, "Нет поля 'answer'"
    assert "tool_calls" in output, "Нет поля 'tool_calls'"
    assert isinstance(output["tool_calls"], list), "'tool_calls' должен быть списком"
    assert output["tool_calls"] == [], "'tool_calls' должен быть пуст для Task 1"
