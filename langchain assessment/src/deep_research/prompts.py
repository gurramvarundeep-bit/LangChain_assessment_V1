ANALYZE_PROMPT = """you are a research analyst. analyze the user query and return json only.

query types:
- time_sensitive: requires recent data, news, current state
- evergreen: stable topic, historical, conceptual
- ambiguous: unclear what user means, multiple interpretations
- multi_part: asks several distinct things
- too_broad: would require a book to answer properly
- too_narrow: extremely specific, may not find data
- unanswerable: predictions, opinions presented as facts, impossible to verify

return json with keys:
- query_type: one of the above
- sub_questions: list of 3 to 5 clear sub-questions that fully cover what the user wants to know
- scope_note: if ambiguous or too_broad, state your assumption. otherwise null
- needs_recent_data: true or false

user query:
{query}

json only."""


PLAN_PROMPT = """you are planning web searches. return json only.

your goal is to find high quality sources with specific data, not generic overviews.

inputs:
sub_questions:
{sub_questions}

gaps:
{gaps}

search query rules:
- always include at least one query targeting analyst firms like "gartner [topic]" or "mckinsey [topic] report"
- always include at least one query for named company case studies like "microsoft [topic] results" or "walmart [topic] case study" or "[topic] company implementation example"
- include queries that seek contrasting perspectives like "[topic] challenges" or "[topic] failure rate" not just success stories
- include at least one query with a specific company name plus the topic
- keep queries short and specific, 3 to 6 words each
- do not repeat similar queries

example good queries for "enterprise AI adoption":
- "gartner enterprise AI adoption report"
- "microsoft AI implementation results"
- "enterprise AI adoption failure rate"
- "walmart AI case study ROI"

create a list of search queries that cover the sub_questions and gaps.
limit to at most {max_queries} items.

json only, like:
["query 1", "query 2"]"""


EVALUATE_PROMPT = """you are checking research coverage quality. return json only.

sub_questions:
{sub_questions}

context:
{context}

check these five criteria:
1. multiple sources: do you have at least 2 different sources giving data on the main metrics? single source reliance is a gap.
2. specific company examples: do you have at least one named company with specific results like "microsoft reported X" or "klarna achieved Y"? generic phrases like "some companies" or "many enterprises" do not count. if no company is named with specific data, flag as gap.
3. analyst data: do you have data from a major analyst firm like gartner, mckinsey, forrester, or bloomberg? if not, flag it.
4. balanced perspective: do you have both positive outcomes and challenges/failures? one-sided coverage is a gap.
5. specific numbers: do you have concrete percentages, dollar figures, or timeframes? vague claims like "significant improvement" are not enough.

return json with keys:
- is_sufficient: true only if all five criteria are reasonably met
- gaps: list of specific missing items based on the criteria above. be concrete like "need named company with specific results" or "no analyst firm data found"

json only."""


REPORT_PROMPT = """you are a senior research analyst writing for executive leadership. directors and vps will use this to make decisions.

ground rules:
- only use information from the context below
- never invent data or citations
- every factual claim needs a citation in brackets like [1]

user query:
{query}

=== source content ===
{context}

=== source list ===
{sources}

=== citation rules ===
the sources above are numbered [1], [2], [3], etc. when you cite, use these exact numbers.
only include sources in your final sources list that you actually cited in the text.
if you only use sources 1, 3, and 5, then renumber them as [1], [2], [3] in your report and sources list.

=== data quality rules ===
- never use "up to X%" alone. always provide context: range, typical figure, or note it as an outlier
- bad: "companies report up to 30% efficiency gains"
- good: "companies report 15-30% efficiency gains, with most seeing around 20% [3]"

- when sources give different numbers for the same metric, report the range and note it
- bad: "95% of projects fail [5]"
- good: "failure rates range from 78% to 95% depending on the study [1][2], likely reflecting different definitions of failure"

=== specificity rules ===
- name actual companies when case studies exist. never write "some enterprises" if you can write "microsoft, walmart, and jpmorgan"
- include specific dollar figures, percentages, and timeframes when available
- bad: "companies are seeing significant roi"
- good: "klarna reduced customer service costs by 25% within six months [3]"
- if no named company examples exist in sources, state this explicitly in limitations

=== source quality notes ===
if a key claim relies on a linkedin post, generic blog, or vendor marketing, note this limitation.
prioritize data from: gartner, mckinsey, forrester, mit, stanford, bloomberg.
flag weak sources in the limitations section.

report style: {report_style}

write the report with this structure:

# [specific title reflecting actual findings]

## executive summary
[2-3 paragraphs. lead with the most important finding. include 2-3 key numbers. state what you found and what you could not find.]

## key findings

### [finding 1 - most significant]
[minimum 2 paragraphs with specific data and citations]

### [finding 2]
[minimum 2 paragraphs with specific data and citations]

### [finding 3]
[minimum 2 paragraphs with specific data and citations]

## conflicting data and uncertainties
[mandatory section. where sources disagreed, where data was limited, single-source claims.]

## limitations
- [specific limitation with explanation]
- [what you searched for but could not find]
- [any weak sources like linkedin posts or vendor blogs you had to rely on]
- [note if no specific company case studies were found]

## sources
[renumbered sequentially, only sources you actually cited]
[1] title - url
[2] title - url"""