def build_decide_prompt(user_input: str) -> list[dict]:
    system_prompt = """
        You are an AI assistant.

        Your task is to decide:
        - Do we have enough information to write Lua code?
        - Or do we need clarification?

        Return ONLY JSON:

        {
        "action": "generate" or "clarify",
        "question": "string"
        }

        Rules:
        - If the task is clear → action = "generate"
        - If unclear → action = "clarify"
        - If clarify → ask ONE short question
        - If generate → question = ""

        Examples:

        User: "Sort an array"
        Output:
        {
        "action": "clarify",
        "question": "What sorting algorithm should be used?"
        }

        User: "Write Lua function for factorial"
        Output:
        {
        "action": "generate",
        "question": ""
        }
    """

    user_prompt = f"User: {user_input}"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]