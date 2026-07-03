from ollama import chat
from src.config import MODEL_NAME, LLM_OPTIONS

class LLMClient:
    def __init__(self):
        self.model = MODEL_NAME
        self.options = LLM_OPTIONS

    def call(self, messages: list[dict]) -> str:
        response = chat(
            model=self.model,
            messages=messages,
            options=self.options,
        )

        # Если модель только загрузилась, значит вызываем снова
        if response.done_reason == "load":
            response = chat(
                model=self.model,
                messages=messages,
                options=self.options,
            )

        return response.message.content or ""