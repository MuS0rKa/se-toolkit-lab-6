#!/usr/bin/env python3
"""
Agent for Task 1: Calls an LLM with a question and returns a JSON response.
"""

import os
import sys
import json
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# --- Загрузка конфигурации ---
env_file: str = ".env.agent.secret"
if not os.path.exists(env_file):
    print(f"Ошибка: Файл {env_file} не найден.", file=sys.stderr)
    sys.exit(1)

load_dotenv(env_file)

API_KEY: Optional[str] = os.getenv("LLM_API_KEY")
API_BASE: Optional[str] = os.getenv("LLM_API_BASE")
MODEL: Optional[str] = os.getenv("LLM_MODEL")

# Проверка с подробным выводом об ошибке
missing_vars: List[str] = []
if not API_KEY:
    missing_vars.append("LLM_API_KEY")
if not API_BASE:
    missing_vars.append("LLM_API_BASE")
if not MODEL:
    missing_vars.append("LLM_MODEL")

if missing_vars:
    error_msg: str = (
        f"Ошибка: Отсутствуют переменные в .env.agent.secret: {', '.join(missing_vars)}"
    )
    print(error_msg, file=sys.stderr)
    print("Убедись, что файл .env.agent.secret содержит:", file=sys.stderr)
    print("  LLM_API_KEY=marsel-qwen-api-key", file=sys.stderr)
    print("  LLM_API_BASE=http://10.93.26.31:42005/v1", file=sys.stderr)
    print("  LLM_MODEL=qwen3-coder-plus", file=sys.stderr)
    sys.exit(1)


# --- Основная логика ---
def main() -> None:
    # 1. Получаем вопрос из аргументов командной строки
    if len(sys.argv) < 2:
        print('Использование: uv run agent.py "Твой вопрос здесь"', file=sys.stderr)
        sys.exit(1)
    question: str = sys.argv[1]

    # 2. Формируем запрос к API
    base_url: str = API_BASE.rstrip("/") if API_BASE else ""  # type: ignore
    url: str = f"{base_url}/chat/completions"

    headers: Dict[str, str] = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    payload: Dict[str, Any] = {
        "model": MODEL,  # type: ignore
        "messages": [{"role": "user", "content": question}],
    }

    # Отладочная информация идет в stderr
    print(f"Отправка вопроса на {url}...", file=sys.stderr)

    # 3. Отправляем запрос с таймаутом 60 секунд
    try:
        response: requests.Response = requests.post(
            url, headers=headers, json=payload, timeout=60
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        print("Ошибка: Превышен таймаут (60 секунд).", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к API: {e}", file=sys.stderr)
        if e.response is not None:
            print(f"Статус: {e.response.status_code}", file=sys.stderr)
            print(f"Тело: {e.response.text}", file=sys.stderr)
        sys.exit(1)

    # 4. Парсим ответ
    try:
        result: Dict[str, Any] = response.json()
        # Правильный доступ: choices[0].message.content
        choices: List[Any] = result.get("choices", [])
        answer_text: str = ""

        if choices and len(choices) > 0:
            message: Dict[str, Any] = choices[0].get("message", {})
            answer_text = message.get("content", "")
        else:
            print("Предупреждение: API вернул пустой ответ", file=sys.stderr)

    except (json.JSONDecodeError, KeyError, IndexError, AttributeError) as e:
        print(f"Ошибка парсинга ответа от API: {e}", file=sys.stderr)
        sys.exit(1)

    # 5. Формируем и выводим JSON в stdout (только это!)
    output: Dict[str, Any] = {
        "answer": answer_text,
        "tool_calls": [],  # Обязательное поле, пустой список
    }

    json_output: str = json.dumps(output, ensure_ascii=False)
    print(json_output)


if __name__ == "__main__":
    main()
