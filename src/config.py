# LLM CONFIG

MODEL_NAME = "qwen2.5-coder:7b" # "qwen2.5:1.5b"

LLM_OPTIONS = {
    "num_ctx": 4096,
    "num_predict": 256,
    "temperature": 0.2
}

# AGENT CONFIG

MAX_FIX_ATTEMPTS = 4

MAX_CLARIFY_ATTEMPTS = 3

DEBUG = False