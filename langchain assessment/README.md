# deep research agent

this project is a simple deep research agent built with langgraph. it takes a user query, performs iterative web searches, evaluates coverage, and writes a structured report grounded in sources.

## prerequisites
- python 3.10+
- openai api key
- tavily api key

## installation
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```


## how to run
```bash
python examples/run_research.py "latest trends in renewable energy storage"
```

## example usage
command:
```bash
python examples/run_research.py "state of lithium sulfur batteries"
```

sample output (truncated):
```
# state of lithium sulfur batteries

## executive summary
... [1]
```

## langgraph studio screenshot
add a screenshot of the agent graph from langsmith studio here: `docs/graph.png` (placeholder)

## notes
- the agent uses tavily for search and gpt-4o for synthesis
- configuration is available via cli flags in `examples/run_research.py`
