import json
import re
from typing import Any


def parse_json_object(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError("LLM response did not contain a JSON object")

    repaired = match.group(0).replace("```json", "").replace("```", "").strip()
    value = json.loads(repaired)
    if not isinstance(value, dict):
        raise ValueError("LLM response JSON is not an object")
    return value
