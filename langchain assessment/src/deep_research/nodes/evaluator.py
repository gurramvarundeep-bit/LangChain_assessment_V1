from langchain_openai import ChatOpenAI
from ..config import get_config
from ..prompts import EVALUATE_PROMPT
from .utils import read_json, normalize_list


def evaluate_coverage(state, config):
    sub_questions = state.get("sub_questions", [])
    context = state.get("processed_context", "")
    if not context.strip():
        return {"is_sufficient": False, "gaps": sub_questions}
    cfg = get_config(config)
    llm = ChatOpenAI(model=cfg.model, temperature=cfg.temperature)
    prompt = EVALUATE_PROMPT.format(
        sub_questions="\n".join(f"- {q}" for q in sub_questions),
        context=context,
    )
    result = llm.invoke(prompt)
    data = read_json(getattr(result, "content", ""), {})
    is_sufficient = bool(data.get("is_sufficient"))
    gaps = normalize_list(data.get("gaps"))
    return {"is_sufficient": is_sufficient, "gaps": gaps}