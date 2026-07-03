class AgentState:
    def __init__(self):
        self.history = []
        self.current_code = None
        self.last_error = None
        self.last_reasoning = None
        self.last_confidence = None

    def add_user(self, text: str):
        self.history.append({"role": "user", "content": text})

    def add_agent(self, text: str):
        self.history.append({"role": "assistant", "content": text})

    def get_history(self):
        return self.history

    def format_history(self) -> str:
        if not self.history:
            return "None"

        return "\n".join(
            f"{item['role']}: {item['content']}" for item in self.history[:-3]
        )

    def set_code(self, code: str | None):
        self.current_code = code

    def get_code(self):
        return self.current_code

    def set_error(self, error: str | None):
        self.last_error = error

    def get_error(self):
        return self.last_error

    def set_reasoning(self, reasoning: str | None):
        self.last_reasoning = reasoning

    def get_reasoning(self):
        return self.last_reasoning
    
    def set_confidence(self, value: float):
        self.last_confidence = value

    def get_confidence(self):
        return self.last_confidence
    
    def get_last_user_input(self):
        for msg in reversed(self.history):
            if msg["role"] == "user":
                return msg["content"]
        return ""