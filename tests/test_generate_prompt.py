from src.prompts.generate import build_generate_prompt

task = "Из списка email получи последний"
context = {
    "wf": {
        "vars": {
            "emails": ["a@mail.com", "b@mail.com"]
        }
    }
}

messages = build_generate_prompt(task, context)

for m in messages:
    print("====", m["role"].upper(), "====")
    print(m["content"])
    print()