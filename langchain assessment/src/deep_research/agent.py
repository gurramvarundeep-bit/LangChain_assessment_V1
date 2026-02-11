from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from .state import AgentState
from .config import AgentConfig
from .nodes import (
    analyze_query,
    plan_searches,
    execute_searches,
    process_results,
    evaluate_coverage,
    synthesize_report,
)


def route_next(state):
    if state.get("is_sufficient"):
        return "synthesize_report"
    if state.get("iteration", 0) >= state.get("max_iterations", 3):
        return "synthesize_report"
    if not state.get("gaps"):
        return "synthesize_report"
    return "plan_searches"


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("analyze_query", analyze_query)
    graph.add_node("plan_searches", plan_searches)
    graph.add_node("execute_searches", execute_searches)
    graph.add_node("process_results", process_results)
    graph.add_node("evaluate_coverage", evaluate_coverage)
    graph.add_node("synthesize_report", synthesize_report)
    graph.set_entry_point("analyze_query")
    graph.add_edge("analyze_query", "plan_searches")
    graph.add_edge("plan_searches", "execute_searches")
    graph.add_edge("execute_searches", "process_results")
    graph.add_edge("process_results", "evaluate_coverage")
    graph.add_conditional_edges(
        "evaluate_coverage",
        route_next,
        {
            "plan_searches": "plan_searches",
            "synthesize_report": "synthesize_report",
        },
    )
    graph.add_edge("synthesize_report", END)
    return graph.compile()


def make_initial_state(query: str, cfg: AgentConfig) -> dict:
    return {
        "messages": [HumanMessage(content=query)],
        "original_query": query,
        "query_type": "",
        "sub_questions": [],
        "search_queries": [],
        "search_results": [],
        "processed_context": "",
        "sources": [],
        "iteration": 0,
        "max_iterations": cfg.max_iterations,
        "gaps": [],
        "is_sufficient": False,
        "report": "",
    }


def run_research(query: str, cfg: AgentConfig | None = None) -> dict:
    config = cfg or AgentConfig()
    graph = build_graph()
    state = make_initial_state(query, config)
    return graph.invoke(state, config={"configurable": config.to_configurable()})