# import subprocess
# import tempfile


# def validate_lua(code: str):
#     with tempfile.NamedTemporaryFile(suffix=".lua", delete=False) as f:
#         f.write(code.encode())
#         file_path = f.name

#     # Проверка синтаксиса
#     syntax_check = subprocess.run(
#         ["luac", "-p", file_path],
#         capture_output=True,
#         text=True
#     )

#     if syntax_check.returncode != 0:
#         return False, syntax_check.stderr

#     # Проверка через luacheck
#     lint_check = subprocess.run(
#         ["luacheck", file_path],
#         capture_output=True,
#         text=True
#     )

#     if lint_check.returncode != 0:
#         return False, lint_check.stdout

#     return True, ""

# src/validator/validator.py

from luaparser import ast


def validate_lua(code: str):
    if not code or len(code.strip()) == 0:
        return False, "Empty code"

    try:
        ast.parse(code)
    except Exception as e:
        return False, f"Syntax error: {str(e)}"

    if "function" not in code:
        return False, "No function definition found"

    return True, ""