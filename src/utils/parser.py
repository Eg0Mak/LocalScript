import json
import re


def clean_json_string(s: str) -> str:
    s = re.sub(r'[\x00-\x1F]+', ' ', s)

    s = s.replace('\n', '\\n')
    s = s.replace('\r', '')

    return s


def extract_json(s: str) -> str:
    start = s.find("{")
    end = s.rfind("}") + 1

    if start == -1 or end == 0:
        raise ValueError(f"No JSON found in: {s}")

    return s[start:end]


def normalize_code(code: str) -> str:
    if not code:
        return code

    code = code.replace("\\n", "\n")

    code = code.replace("\\t", "\t")
    code = code.replace("\\r", "")

    code = re.sub(r'\\(?!["ntr\\])', '', code)

    return code.strip()


def parse_json(response: str) -> dict:
    if not response or response.strip() == "":
        raise ValueError("Empty response from LLM")

    response = response.strip()

    if response.startswith("```"):
        parts = response.split("```")
        if len(parts) >= 2:
            response = parts[1]
            if response.startswith("json"):
                response = response[4:].strip()

    try:
        data = json.loads(response)
    except:
        pass
    else:
        if "code" in data:
            data["code"] = normalize_code(data["code"])
        return data

    cleaned = clean_json_string(response)
    try:
        data = json.loads(cleaned)
    except:
        pass
    else:
        if "code" in data:
            data["code"] = normalize_code(data["code"])
        return data

    extracted = extract_json(response)
    extracted = clean_json_string(extracted)

    try:
        data = json.loads(extracted)
    except Exception as e:
        raise ValueError(f"Failed to parse JSON:\n{response}") from e

    if "code" in data:
        data["code"] = normalize_code(data["code"])

    return data