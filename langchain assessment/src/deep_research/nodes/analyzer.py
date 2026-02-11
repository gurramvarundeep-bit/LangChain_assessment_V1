from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from ..config import get_config
from ..prompts import ANALYZE_PROMPT
from .utils import read_json, normalize_list


def analyze_query(state, config):
    cfg = get_config(config)
    messages = state.get("messages", [])
    query = state.get("original_query")
    if not query:
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                query = msg.content
                break
    query = query or ""
    llm = ChatOpenAI(model=cfg.model, temperature=cfg.temperature)
    result = llm.invoke(ANALYZE_PROMPT.format(query=query))
    data = read_json(getattr(result, "content", ""), {})
    sub_questions = normalize_list(data.get("sub_questions"))
    if not sub_questions:
        sub_questions = [query] if query else []
    query_type = data.get("query_type") or "evergreen"
    scope_note = data.get("scope_note") or ""
    gaps = state.get("gaps", [])
    if scope_note:
        gaps = gaps + [scope_note]
    return {
        "original_query": query,
        "sub_questions": sub_questions,
        "query_type": query_type,
        "gaps": gaps,
    }