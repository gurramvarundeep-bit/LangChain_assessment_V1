from ..config import get_config
from ..tools import run_search


def is_time_sensitive(query_type: str, query: str) -> bool:
    if query_type == "time_sensitive":
        return True
    text = (query or "").lower()
    flags = ["latest", "recent", "today", "this week", "this month", "2025", "2026"]
    return any(f in text for f in flags)


def execute_searches(state, config):
    cfg = get_config(config)
    queries = state.get("search_queries", [])
    query_type = state.get("query_type", "")
    original_query = state.get("original_query", "")
    days = 30 if is_time_sensitive(query_type, original_query) else 365
    
    search_results = []
    gaps = state.get("gaps", [])
    
    for q in queries[:cfg.max_searches_per_iteration]:
        result = run_search(q, max_results=cfg.max_searches_per_iteration, days=days, provider=cfg.search_provider)
        used_query = q
        
        if not result.get("results"):
            alt = f"{q} overview"
            retry = run_search(alt, max_results=cfg.max_searches_per_iteration, days=days, provider=cfg.search_provider)
            if retry.get("results"):
                result = retry
                used_query = alt
        
        if result.get("error"):
            gaps = gaps + [f"search error for '{used_query}': {result['error']}"]
        
        search_results.append({"query": used_query, "results": result.get("results", [])})
    
    return {"search_results": search_results, "gaps": gaps}