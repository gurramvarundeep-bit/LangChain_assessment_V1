from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    original_query: str
    query_type: str
    sub_questions: list[str]
    search_queries: list[str]
    search_results: list[dict]
    processed_context: str
    sources: list[dict]
    iteration: int
    max_iterations: int
    gaps: list[str]
    is_sufficient: bool
    report: str