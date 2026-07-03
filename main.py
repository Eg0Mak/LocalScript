from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import asyncio
from concurrent.futures import ThreadPoolExecutor

from src.agent.agent import Agent


app = FastAPI(
    title="LocalScript API",
    version="1.0.0",
)

executor = ThreadPoolExecutor()
agent = Agent()


sessions = {}

MAX_TOKENS = 3000

def estimate_tokens(messages):
    total_chars = sum(len(m["content"]) for m in messages)
    return total_chars // 4


def trim_history(messages):
    while len(messages) > 2 and estimate_tokens(messages) > MAX_TOKENS:
        # удаляем пару user + agent
        messages.pop(0)
        messages.pop(0)
    return messages


class ChatRequest(BaseModel):
    session_id: str
    message: str


@app.get("/")
async def root():
    return {"message": "service is running"}


@app.post("/chat")
async def chat(body: ChatRequest):
    if not body.message.strip():
        raise HTTPException(status_code=422, detail="message не может быть пустым")

    session_id = body.session_id

    if session_id not in sessions:
        sessions[session_id] = []

    sessions[session_id].append({
        "role": "user",
        "content": body.message
    })

    sessions[session_id] = trim_history(sessions[session_id])

    messages = sessions[session_id]

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        executor,
        lambda: agent.chat(messages)
    )

    # если агент задал вопрос
    if result["status"] == "clarify":
        sessions[session_id].append({
            "role": "agent",
            "content": result["question"]
        })

    return result


@app.post("/reset")
async def reset(session_id: str):
    sessions.pop(session_id, None)
    return {"status": "reset"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)