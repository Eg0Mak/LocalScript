from src.agent.state import AgentState
from src.config import DEBUG, MAX_CLARIFY_ATTEMPTS, MAX_FIX_ATTEMPTS
from src.llm.llm import LLMClient
from src.prompts.fix import build_fix_prompt
from src.prompts.generate import build_generate_prompt
from src.prompts.planner import build_planner_prompt
from src.utils.parser import parse_json
from src.validator.validator import validate_lua


class Agent:
    def __init__(self):
        self.llm = LLMClient()
        self.tools = {
            "generate": self._tool_generate,
            "fix": self._tool_fix,
            "clarify": self._tool_clarify,
            "done": self._tool_done,
        }


    def _tool_generate(self, state: AgentState, **kwargs):
        task_text = state.get_last_user_input()
        raw = self.llm.call(build_generate_prompt(task_text))
        return parse_json(raw)


    def _tool_fix(self, state: AgentState, **kwargs):
        raw = self.llm.call(
            build_fix_prompt(
                task=state.get_last_user_input(),
                code=state.get_code(),
                error=state.get_error(),
            )
        )
        return parse_json(raw)


    def _tool_clarify(self, state: AgentState, message: str = "", **kwargs):
        return {
            "status": "clarify",
            "question": message
        }


    def _tool_done(self, state: AgentState, **kwargs):
        return {"status": "done"}


    def chat_cli(self):
        print("LocalScript Agent")
        print("Type 'exit' to quit\n")

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() == "exit":
                break

            state = AgentState()
            state.add_user(user_input)

            result = self.run_loop(state)

            print("Status:", result["status"])

            if result.get("reasoning"):
                print("Planner reasoning:", result["reasoning"])

            if result.get("code"):
                print("Code:\n", result["code"])

            if result.get("explanation"):
                print("\nExplanation:", result["explanation"])

            if result.get("error"):
                print("\nError:", result["error"])

            print(f"Confidence: {state.get_confidence():.2f}")
            print("\n" + "-" * 40 + "\n")

    def chat(self, messages: list[dict]) -> dict:
        state = AgentState()

        for msg in messages:
            if msg["role"] == "user":
                state.add_user(msg["content"])
            else:
                state.add_agent(msg["content"])

        result = self.run_loop(state)
        result["confidence"] = state.get_confidence()

        return result


    def run_loop(self, state: AgentState) -> dict:
        fix_attempts = 0
        clarify_attempts = 0
        last_explanation = ""

        while True:
            planner_raw = self.llm.call(build_planner_prompt(state))
            plan = parse_json(planner_raw)

            if plan.get("type") == "tool_call":
                tool_name = plan.get("name")
                args = plan.get("arguments", {})
                confidence = float(plan.get("confidence", 1.0))

                state.set_confidence(confidence)
                state.set_reasoning(plan.get("reasoning", ""))

                if DEBUG:
                    print(f"[DEBUG] Tool call: {tool_name}")
                    print(f"[DEBUG] Confidence: {confidence}")

                if tool_name not in self.tools:
                    return {
                        "status": "failed",
                        "error": f"Unknown tool: {tool_name}"
                    }

                tool = self.tools[tool_name]
                result = tool(state, **args)

                if tool_name == "clarify":
                    if clarify_attempts >= MAX_CLARIFY_ATTEMPTS:
                        return {
                            "status": "failed",
                            "code": state.get_code(),
                            "explanation": last_explanation,
                            "error": "Max clarification attempts reached",
                            "reasoning": state.get_reasoning(),
                        }

                    question = result.get("question", "")
                    state.add_agent(question)

                    return {
                        "status": "clarify",
                        "question": question,
                        "reasoning": state.get_reasoning(),
                        "confidence": state.get_confidence(),
                    }

                if tool_name == "generate":
                    code = result.get("code", "")
                    explanation = result.get("explanation", "")

                    state.set_code(code)
                    state.set_error(None)
                    last_explanation = explanation

                    valid, error = validate_lua(code)
                    if not valid:
                        state.set_error(error)
                    
                    if valid:
                        state.set_error(None)
                        continue

                    if not code.strip():
                        state.set_error("empty code")

                    continue

                if tool_name == "fix":
                    if fix_attempts >= MAX_FIX_ATTEMPTS:
                        return {
                            "status": "failed",
                            "code": state.get_code(),
                            "explanation": last_explanation,
                            "error": state.get_error(),
                            "reasoning": state.get_reasoning(),
                        }

                    code = result.get("code", state.get_code())
                    explanation = result.get("explanation", "")

                    state.set_code(code)
                    last_explanation = explanation

                    valid, error = validate_lua(code)
                    if valid:
                        state.set_error(None)
                    else:
                        state.set_error(error)

                    fix_attempts += 1
                    continue

                if tool_name == "done":
                    return {
                        "status": "success" if state.get_code() else "failed",
                        "code": state.get_code(),
                        "explanation": last_explanation,
                        "error": state.get_error(),
                        "reasoning": state.get_reasoning(),
                    }

            action = plan.get("action", "")
            message = plan.get("message", "")
            reasoning = plan.get("reasoning", "")
            confidence = float(plan.get("confidence", 1.0))

            state.set_reasoning(reasoning)
            state.set_confidence(confidence)

            if DEBUG:
                print(f"[DEBUG] Planner action: {action}")
                print(f"[DEBUG] Planner reasoning: {reasoning}")
                print(f"[DEBUG] Confidence: {confidence}")


            if action == "clarify":
                if clarify_attempts >= MAX_CLARIFY_ATTEMPTS:
                    return {
                        "status": "failed",
                        "code": state.get_code(),
                        "explanation": last_explanation,
                        "error": "Max clarification attempts reached",
                        "reasoning": state.get_reasoning(),
                    }

                state.add_agent(message)

                return {
                    "status": "clarify",
                    "question": message,
                    "reasoning": state.get_reasoning(),
                    "confidence": state.get_confidence(),
                }

            if action == "generate":
                if state.get_code() and not state.get_error():
                    if DEBUG:
                        print("[DEBUG] Skipping redundant legacy generate")
                    continue

                task_text = state.format_history()
                generate_raw = self.llm.call(build_generate_prompt(task_text))

                if DEBUG:
                    print("\n[DEBUG] Generate raw:", generate_raw)

                parsed = parse_json(generate_raw)

                code = parsed.get("code", "")
                explanation = parsed.get("explanation", "")

                state.set_code(code)
                last_explanation = explanation

                valid, error = validate_lua(code)

                if valid:
                    state.set_error(None)
                else:
                    state.set_error(error)

                continue

            if action == "fix":
                if fix_attempts >= MAX_FIX_ATTEMPTS:
                    return {
                        "status": "failed",
                        "code": state.get_code(),
                        "explanation": last_explanation,
                        "error": state.get_error(),
                        "reasoning": state.get_reasoning(),
                    }

                fix_raw = self.llm.call(
                    build_fix_prompt(
                        task=state.get_last_user_input(),
                        code=state.get_code(),
                        error=state.get_error(),
                    )
                )

                if DEBUG:
                    print("\n[DEBUG] Fix raw:", fix_raw)

                parsed = parse_json(fix_raw)

                code = parsed.get("code", state.get_code())
                explanation = parsed.get("explanation", "")

                state.set_code(code)
                last_explanation = explanation

                valid, error = validate_lua(code)

                if valid:
                    state.set_error(None)
                else:
                    state.set_error(error)

                fix_attempts += 1
                continue

            if action == "done":
                return {
                    "status": "success" if state.get_code() else "failed",
                    "code": state.get_code(),
                    "explanation": last_explanation,
                    "error": state.get_error(),
                    "reasoning": state.get_reasoning(),
                }

            return {
                "status": "failed",
                "code": state.get_code(),
                "explanation": last_explanation,
                "error": f"Unknown planner action: {action}",
                "reasoning": state.get_reasoning(),
            }