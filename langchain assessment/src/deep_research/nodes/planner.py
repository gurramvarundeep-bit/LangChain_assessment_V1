from langchain_openai import ChatOpenAI
from ..config import get_config
from ..prompts import PLAN_PROMPT
from .utils import read_json, normalize_list


def plan_searches(state, config):
    cfg = get_config(config)
    sub_questions = state.get("sub_questions", [])
    gaps = state.get("gaps", [])
    llm = ChatOpenAI(model=cfg.model, temperature=cfg.temperature)
    prompt = PLAN_PROMPT.format(
        sub_questions="\n".join(f"- {q}" for q in sub_questions),
        gaps="\n".join(f"- {g}" for g in gaps),
        max_queries=cfg.max_searches_per_iteration,
    )
    result = llm.invoke(prompt)
    data = read_json(getattr(result, "content", ""), [])
    queries = normalize_list(data)
    if not queries:
        queries = sub_questions[: cfg.max_searches_per_iteration]
    iteration = state.get("iteration", 0) + 1
    return {"search_queries": queries, "iteration": iteration}