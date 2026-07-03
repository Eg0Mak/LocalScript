<div align="center">

# LocalScript

### Local AI Agent for Lua Code Generation

**Локальный AI-агент, который превращает задачу на естественном языке в валидный Lua-код, проверяет результат и автоматически исправляет ошибки через agent loop.**

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-local%20LLM-000000?style=for-the-badge)
![Lua](https://img.shields.io/badge/Lua-validation-2C2D72?style=for-the-badge&logo=lua&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)

</div>

---

## About

**LocalScript** - это backend-проект про локальную LLM-инженерию: FastAPI-сервис принимает пользовательскую задачу, агент планирует следующий шаг, генерирует Lua-код через Ollama, проверяет его через `luac` и при ошибках запускает цикл исправления.

Проект сделан без внешних AI API и без тяжелых orchestration-фреймворков. Вместо этого здесь прозрачный agent loop, контролируемые промпты, устойчивый JSON parsing и воспроизводимый запуск через Docker.

Для рекрутера этот проект показывает не только умение подключить LLM, но и инженерную работу вокруг нее: state management, validation, retry/fix loop, API design, контейнеризацию и работу с ограничениями локальных моделей.

---

## Highlights

- **Local-first AI**: inference работает через Ollama, без облачных LLM API.
- **Agent loop**: planner выбирает действие `generate`, `fix`, `clarify` или `done`.
- **Self-healing generation**: если Lua-код не проходит проверку, агент передает ошибку модели и пробует исправить код.
- **Lua validation**: синтаксис проверяется через `luac`, есть отдельная runtime-проверка через `lua`.
- **Session memory**: FastAPI хранит историю по `session_id` и обрезает контекст при превышении лимита.
- **Robust parsing**: отдельный parser восстанавливает JSON даже из частично загрязненных ответов модели.
- **Docker-ready**: сервис, Ollama и загрузка модели описаны в `docker-compose.yml`.
- **Minimal dependencies**: агент написан вручную, без LangChain/LangGraph, чтобы сохранить контроль над поведением.

---

## How It Works

```text
User
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
  +--> clarify  -> ask one short question
  +--> generate -> create Lua code with Ollama
  +--> fix      -> repair code using validator error
  +--> done     -> return final result
  |
  v
Lua validator
  |
  v
JSON response
```

The core idea is simple: **the model does not just generate code once**. It works inside a controlled loop where every result is parsed, validated and either returned or sent back for repair.

---

## Tech Stack

| Area | Tools |
| --- | --- |
| API | FastAPI, Pydantic, Uvicorn |
| Local LLM | Ollama, `qwen2.5-coder:7b` |
| Agent runtime | Custom Python agent loop |
| Validation | `luac`, `lua`, subprocess timeouts |
| Packaging | Docker, Docker Compose |
| Testing | Pytest-compatible project structure |

---

## Project Structure

```text
.
├── main.py                     # FastAPI app and HTTP endpoints
├── requirements.txt
├── docker/
│   ├── Dockerfile              # Python service image
│   └── docker-compose.yml      # Ollama + model init + agent service
├── data/
│   ├── examples/fewshot.json   # Few-shot examples for generation
│   └── tasks/dataset_seed.jsonl
├── src/
│   ├── agent/
│   │   ├── agent.py            # Agent loop and tool execution
│   │   └── state.py            # Conversation state, code, errors, confidence
│   ├── llm/llm.py              # Ollama client wrapper
│   ├── prompts/
│   │   ├── planner.py          # Action selection prompt
│   │   ├── generate.py         # Lua generation prompt
│   │   ├── fix.py              # Error-aware repair prompt
│   │   └── decide.py
│   ├── utils/parser.py         # Defensive JSON extraction and normalization
│   ├── validator/validator.py  # Lua syntax/runtime validation helpers
│   └── config.py               # Model and agent settings
└── tests/
    └── test_generate_prompt.py
```

---

## Quick Start

### 1. Run with Docker Compose

```bash
cd docker
docker compose up --build
```

The compose setup starts:

- `ollama` on port `11434`;
- `model-init`, which pulls `qwen2.5-coder:7b`;
- `agent` on port `8080`.

### 2. Check the service

```bash
curl http://localhost:8080/
```

Expected response:

```json
{
  "message": "service is running"
}
```

### 3. Generate Lua code

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo-user",
    "message": "Напиши Lua-функцию для факториала"
  }'
```

Example response shape:

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

---

## API

### `GET /`

Health check endpoint.

### `POST /chat`

Generates, validates or repairs Lua code for a user message.

Request:

```json
{
  "session_id": "user-1",
  "message": "Отфильтруй массив пользователей старше 18 лет"
}
```

Possible statuses:

| Status | Meaning |
| --- | --- |
| `success` | Code was generated and passed validation |
| `clarify` | Agent needs one clarification question answered |
| `failed` | Agent could not produce a valid result within limits |

### `POST /reset`

Clears server-side memory for a session.

---

## Agent Design

The agent is intentionally implemented without a heavy framework. This keeps every decision visible:

1. **Planner prompt** inspects conversation state, current code and last validation error.
2. **Tool dispatcher** calls one of the internal tools: generation, repair, clarification or completion.
3. **LLM client** sends structured prompts to Ollama.
4. **Parser** extracts and normalizes JSON responses.
5. **Validator** checks generated Lua code.
6. **Loop controller** repeats repair attempts until code is valid or the configured limit is reached.

Key limits are configured in `src/config.py`:

```python
MODEL_NAME = "qwen2.5-coder:7b"
MAX_FIX_ATTEMPTS = 4
MAX_CLARIFY_ATTEMPTS = 3
```

---

## Why This Project Is Interesting

This repository focuses on problems that appear in real LLM products:

- local model constraints and short output budgets;
- unreliable structured output from LLMs;
- separating planning from execution;
- preventing infinite clarification/fix loops;
- validating generated code before returning it to the user;
- keeping API state on the server side;
- making the system reproducible for demos and review.

In other words, LocalScript is not just a prompt wrapper. It is a small, inspectable agentic system built around reliability.

---

## Roadmap

- Add automated endpoint tests for `/chat` and `/reset`.
- Expand Lua validation with sandboxed runtime checks in the main agent path.
- Add benchmark reports for generated code quality.
- Support model selection through environment variables.
- Add persistent session storage for production-like deployments.

---

## Author

Built as a local AI engineering project focused on **agent architecture, validation loops and practical LLM reliability**.
