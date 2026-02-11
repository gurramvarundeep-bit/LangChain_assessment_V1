from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from ..config import get_config
from ..prompts import REPORT_PROMPT

def build_source_list(sources):
    lines = []
    for i, s in enumerate(sources, 1):
        lines.append(f"[{i}] {s.get('title', '')} - {s.get('url', '')}")
    return "\n".join(lines)

def synthesize_report(state, config):
    cfg = get_config(config)
    query = state.get("original_query", "")
    sources = state.get("sources", [])
    context = state.get("processed_context", "")

    if not sources:
        report = "# report\n\n## executive summary\nno sources were found to answer the query.\n\n## key findings\n\n### insufficient sources\nno factual findings can be supported without sources.\n\n## conflicting data and uncertainties\nno data available to analyze.\n\n## limitations\n- no sources were returned from search\n- the report cannot provide grounded facts\n\n## sources\nnone"
        return {"report": report, "messages": [AIMessage(content=report)]}
    sources_text = build_source_list(sources)
    prompt = REPORT_PROMPT.format(
        report_style=cfg.report_style,
        query=query,
        context=context,
        sources=sources_text,
    )

    llm = ChatOpenAI(model=cfg.model, temperature=cfg.temperature)
    result = llm.invoke(prompt)
    report = getattr(result, "content", "").strip()

    if not report:
        report = "# report\n\n## executive summary\nreport generation failed.\n\n## key findings\n\n### insufficient output\nthe model did not return content.\n\n## conflicting data and uncertainties\nno data available.\n\n## limitations\n- report generation failed\n\n## sources\n" + sources_text
    return {"report": report, "messages": [AIMessage(content=report)]}