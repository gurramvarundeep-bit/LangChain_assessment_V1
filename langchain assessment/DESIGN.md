# design notes

i went with a plan → execute → reflect loop because i wanted something more structured than a free-form react loop, but still iterative. the linear pipeline felt too brittle for multi-part queries. the loop lets me check coverage, surface gaps, and decide when to stop without spinning forever.

what worked well:
- langgraph made it easy to express the loop and the conditional routing
- keeping prompts in one place made iteration fast
- the tavily wrapper with retries handled rough edges in search pretty cleanly

what didn’t work at first and how i fixed it:
- the analyzer output was messy when the llm returned extra text. i added a small json extractor to clean that up
- i initially let the evaluator return “maybe” states which made routing fuzzy. i tightened it to a strict boolean

tradeoffs i made:
- i kept the state schema simple even though there are a few extra fields that could help debugging
- i defaulted to a single report style instead of a richer style system to keep the config light

known limitations:
- the report quality depends heavily on search results quality
- if search returns nothing, the report can only say it found nothing
- the evaluator can miss subtle gaps if the context is vague

what i’d add with more time:
- a lightweight source credibility scorer
- more aggressive deduping and clustering for long result lists
- a separate “assumptions” section in the report when the query is ambiguous

performance ideas:
- caching search results by query to avoid repeated calls
- parallelizing searches within an iteration
- shorter context summaries to reduce token use