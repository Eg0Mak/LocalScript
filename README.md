<div align="center">

# LocalScript

### Local AI Agent for Lua Code Generation

**Локальный AI-агент для генерации, проверки и автоматического исправления Lua-кода через управляемый agent loop.**

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-000000?style=for-the-badge)
![Lua](https://img.shields.io/badge/Lua-Code%20Validation-2C2D72?style=for-the-badge&logo=lua&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)

</div>

---

## Overview

**LocalScript** - это backend-сервис, который превращает пользовательский запрос на естественном языке в рабочий Lua-код. Агент не просто один раз вызывает модель: он планирует следующий шаг, генерирует решение, валидирует результат и при ошибках запускает цикл исправления.

Проект построен вокруг локального inference через **Ollama** и модели **qwen2.5-coder:7b**. Внешние AI API не используются, поэтому систему можно запускать и демонстрировать в изолированной среде.

Главная идея проекта - показать практичную LLM-инженерию: не красивую обертку над промптом, а контролируемый пайплайн с состоянием, валидацией, ограничениями, retry logic и понятной архитектурой.

---

## What Makes It Strong

- **Local-first architecture**: генерация работает локально через Ollama, без OpenAI API, Anthropic API или других облачных провайдеров.
- **Custom agent loop**: агент написан вручную, без LangChain и LangGraph, поэтому логика принятия решений полностью прозрачна.
- **Planner + tools pattern**: planner выбирает действие, а tools выполняют конкретные шаги: `generate`, `fix`, `clarify`, `done`.
- **Validation-driven generation**: сгенерированный Lua-код проверяется перед возвратом пользователю.
- **Self-repair flow**: если validator находит ошибку, агент передает ее обратно модели и просит исправить уже существующий код.
- **Session memory**: API хранит историю диалога по `session_id` и обрезает контекст при превышении лимита.
- **Robust JSON parsing**: отдельный parser вытаскивает JSON даже из неидеальных ответов модели.
- **Docker-ready demo**: сервис, Ollama и загрузка модели описаны в Docker Compose.

---

## Architecture

```text
User request
    |
    v
FastAPI /chat
    |
    v
Session memory + context trimming
    |
    v
Agent planner
    |
    +--> clarify  -> one short clarification question
    +--> generate -> Lua code generation
    +--> fix      -> error-aware code repair
    +--> done     -> final response
    |
    v
Lua validator
    |
    v
Structured JSON response
```

Такой подход делает поведение агента предсказуемым: модель отвечает не произвольным текстом, а структурированным JSON, а каждое действие проходит через контролируемую Python-логику.

---

## Tech Stack

| Area | Technologies |
| --- | --- |
| API | FastAPI, Pydantic, Uvicorn |
| Local LLM | Ollama, qwen2.5-coder:7b |
| Agent Runtime | Custom Python agent loop |
| Prompting | Planner prompt, generation prompt, fix prompt |
| Validation | luac, lua, subprocess timeouts |
| State | Server-side session memory |
| Packaging | Docker, Docker Compose |

---

## Core Flow

```text
generate -> validate -> fix -> validate -> done
```

Агент работает итеративно:

1. **Planner** анализирует историю, текущий код и последнюю ошибку.
2. **Generator** создает компактный Lua-код в строгом JSON-формате.
3. **Validator** проверяет синтаксис через `luac`.
4. **Fixer** получает исходную задачу, текущий код и текст ошибки.
5. **Agent loop** повторяет исправление до успешной проверки или достижения лимита.

Это приближает проект к реальному coding assistant, где важен не сам факт генерации, а способность дойти до валидного результата.

---

## API

### `GET /`

Проверка, что сервис запущен.

```json
{
  "message": "service is running"
}
```

### `POST /chat`

Основной endpoint для работы с агентом.

Request:

```json
{
  "session_id": "demo-user",
  "message": "Напиши Lua-функцию для факториала"
}
```

Response:

```json
{
  "status": "success",
  "code": "function factorial(n)\n    if n == 0 then return 1 end\n    return n * factorial(n - 1)\nend",
  "explanation": "Recursive factorial implementation",
  "error": null,
  "reasoning": "Valid code is already available.",
  "confidence": 0.9
}
```

Possible statuses:

| Status | Description |
| --- | --- |
| `success` | код успешно создан и прошел проверку |
| `clarify` | агенту нужно одно уточнение от пользователя |
| `failed` | агент не смог получить валидный результат в заданных лимитах |

### `POST /reset`

Сброс server-side memory для выбранной сессии.

---

## Quick Start

### Docker Compose

```bash
cd docker
docker compose up --build
```

После запуска будут подняты:

- **ollama** на порту `11434`;
- **model-init** для загрузки `qwen2.5-coder:7b`;
- **agent** на порту `8080`.

Проверка API:

```bash
curl http://localhost:8080/
```

Пример запроса:

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo-user",
    "message": "Сделай Lua-код для сортировки массива чисел"
  }'
```

---

## Project Structure

```text
.
├── main.py                     # FastAPI app, endpoints, session memory
├── requirements.txt
├── docker/
│   ├── Dockerfile              # Python service image
│   └── docker-compose.yml      # Ollama + model init + agent service
├── data/
│   ├── examples/fewshot.json   # few-shot examples for generation
│   └── tasks/dataset_seed.jsonl
├── src/
│   ├── agent/
│   │   ├── agent.py            # main agent loop and tool dispatcher
│   │   └── state.py            # conversation state, code, errors, confidence
│   ├── llm/
│   │   └── llm.py              # Ollama client wrapper
│   ├── prompts/
│   │   ├── planner.py          # action selection prompt
│   │   ├── generate.py         # Lua generation prompt
│   │   ├── fix.py              # validation-aware repair prompt
│   │   └── decide.py
│   ├── utils/
│   │   └── parser.py           # defensive JSON extraction and normalization
│   ├── validator/
│   │   └── validator.py        # Lua validation helpers
│   └── config.py               # model and agent settings
└── tests/
    └── test_generate_prompt.py
```

---

## Engineering Decisions

### No Heavy Orchestration Framework

Агентная логика реализована вручную. Это делает проект проще для отладки и честнее для демонстрации: видно, где planner принимает решение, где вызывается модель, где парсится ответ и где происходит validation.

### Structured Output

Модель должна возвращать JSON с полями `code` и `explanation`. Так API получает не свободный текст, а предсказуемую структуру, которую можно валидировать и отдавать клиенту.

### Defensive Parser

Локальные модели не всегда идеально соблюдают формат. Поэтому parser умеет убирать markdown fences, извлекать JSON из ответа, чистить control characters и нормализовать переносы строк внутри кода.

### Validation Before Response

Система не доверяет результату модели на слово. Lua-код проходит проверку через `luac`, а ошибка сохраняется в state и используется на следующей итерации исправления.

### Controlled Limits

В `src/config.py` заданы ограничения на модель и поведение агента:

```python
MODEL_NAME = "qwen2.5-coder:7b"

LLM_OPTIONS = {
    "num_ctx": 4096,
    "num_predict": 256,
    "temperature": 0.2
}

MAX_FIX_ATTEMPTS = 4
MAX_CLARIFY_ATTEMPTS = 3
```

Эти лимиты помогают избежать бесконечных циклов и делают поведение сервиса более предсказуемым.

---

## Why It Matters

LocalScript показывает несколько важных навыков, которые полезны в реальной backend и AI engineering разработке:

- проектирование agentic workflow без магии фреймворков;
- работа с локальными open-source моделями;
- prompt engineering под строгий JSON output;
- обработка нестабильных LLM-ответов;
- server-side memory и context trimming;
- subprocess-based validation;
- контейнеризация AI-сервиса;
- умение превращать эксперимент с моделью в воспроизводимый API.

---

## Roadmap

- Добавить полноценные endpoint tests для `/chat` и `/reset`.
- Подключить runtime validation в основной путь агента.
- Вынести `MODEL_NAME` в environment variables.
- Добавить benchmark report по качеству генерации.
- Реализовать persistent session storage.
- Добавить UI-клиент для демонстрации agent loop.

---

## Author

Проект собран как демонстрация практической AI engineering разработки: локальная LLM, управляемый agent loop, validation-first подход и аккуратный backend API.
