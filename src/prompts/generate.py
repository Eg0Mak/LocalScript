import json
from pathlib import Path


FEWSHOT_PATH = Path(__file__).resolve().parents[2] / "data" / "examples" / "fewshot.json"


FALLBACK_EXAMPLES = [
    {
        "task": "Добавь переменную с квадратом числа.",
        "output": {
            "code": "local n = tonumber('5')\\nreturn n * n",
            "explanation": "Calculates square of a number"
        },
    },
    {
        "task": "Отфильтруй элементы из массива, чтобы включить только те, у которых есть значения в полях Discount или Markdown.",
        "output": {
            "code": "local result = {}\\nfor _, item in ipairs(wf.vars.parsedCsv) do\\n    if (item.Discount ~= '' and item.Discount ~= nil) or (item.Markdown ~= '' and item.Markdown ~= nil) then\\n        table.insert(result, item)\\n    end\\nend\\nreturn result",
            "explanation": "Filters items based on Discount or Markdown fields"
        },
    },
    {
        "task": "Write Lua function for factorial",
        "output": {
            "code": "function factorial(n)\\n    if n == 0 then return 1 end\\n    return n * factorial(n - 1)\\nend",
            "explanation": "Recursive factorial implementation"
        },
    },
]


def load_fewshot() -> list[dict]:
    try:
        if not FEWSHOT_PATH.exists():
            return FALLBACK_EXAMPLES

        with open(FEWSHOT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            examples = data.get("generation", [])
        elif isinstance(data, list):
            examples = data
        else:
            return FALLBACK_EXAMPLES

        normalized = []
        for ex in examples:
            task = ex.get("task") or ex.get("user_request")
            output = ex.get("output")

            if output is None and "lua_code" in ex:
                output = {
                    "code": ex["lua_code"],
                    "explanation": "Lua solution"
                }

            if not task or not output or "code" not in output:
                continue

            normalized.append({
                "task": task,
                "output": {
                    "code": str(output.get("code", "")),
                    "explanation": str(output.get("explanation", "Lua solution")),
                },
            })

        return normalized[:3] if normalized else FALLBACK_EXAMPLES

    except Exception:
        return FALLBACK_EXAMPLES


def format_example(example: dict) -> str:
    output_json = json.dumps(example["output"], ensure_ascii=False)

    return f"""
        Input:
        {example["task"]}

        Output:
        {output_json}
    """.strip()


def build_generate_prompt(task: str) -> list[dict]:
    examples = load_fewshot()[:3]
    formatted_examples = "\n\n".join(format_example(e) for e in examples)

    system_prompt = f"""
        You are an AI agent that generates correct and executable Lua code.

        STRICT OUTPUT RULES:
        - Return ONLY a valid JSON object
        - Do NOT include markdown (``` or ```json)
        - Do NOT include any text outside JSON
        - JSON must be strictly valid and parseable

        OUTPUT FORMAT:
        {{
        "code": "string (valid Lua code)",
        "explanation": "short explanation"
        }}

        CODE REQUIREMENTS:
        - Code MUST be valid Lua syntax
        - Code MUST fully solve the task
        - Code MUST be formatted with proper indentation and line breaks
        - Code MUST be readable (multi-line, not one-line)
        - Use idiomatic Lua (local variables, loops, functions)
        - Avoid unnecessary complexity
        - Ensure mathematical correctness for algorithms
        - If solving systems, correctly use matrix inversion or linear solvers
        - Keep the solution concise
        - Do NOT generate helper functions unless absolutely necessary
        - Prefer a minimal implementation over a complete framework
        - If the task is complex, return a compact core implementation
        - Do NOT leave unfinished code
        - Do NOT output partial code
        - If the full solution may be too long, return the smallest working version
        - Avoid long comments and verbose naming
        
        IMPORTANT:
        - Keep the code SHORT
        - Maximum 25 lines
        - Do NOT write multiple functions unless necessary
        - Prefer simple implementation
        - Ensure FULL valid JSON output

        IMPORTANT JSON RULES:
        - Escape all quotes inside the code using \\"
        - Use \\n for line breaks inside the string
        - Do NOT include raw newlines inside JSON strings

        BEHAVIOR RULES:
        - If task is ambiguous, make a reasonable assumption and proceed
        - Do NOT ask questions
        - Always return working code
        - Do NOT mention fixes or errors in explanation unless explicitly fixing code

        EXAMPLES:
        {formatted_examples}
    """.strip()

    user_prompt = f"""
        Task:
        {task}
    """.strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]