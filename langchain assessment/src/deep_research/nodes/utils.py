import json
import re


def read_json(text: str, fallback):
    if not text:
        return fallback
    try:
        return json.loads(text)
    except Exception:
        pass
    obj_start = text.find("{")
    obj_end = text.rfind("}")
    if obj_start != -1 and obj_end != -1 and obj_end > obj_start:
        try:
            return json.loads(text[obj_start:obj_end + 1])
        except Exception:
            pass
    arr_start = text.find("[")
    arr_end = text.rfind("]")
    if arr_start != -1 and arr_end != -1 and arr_end > arr_start:
        try:
            return json.loads(text[arr_start:arr_end + 1])
        except Exception:
            pass
    return fallback


def normalize_list(value):
    if isinstance(value, list):
        return [v for v in value if isinstance(v, str) and v.strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []