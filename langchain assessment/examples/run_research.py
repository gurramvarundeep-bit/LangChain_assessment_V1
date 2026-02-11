import argparse
import sys
from dotenv import load_dotenv
from deep_research import run_research, AgentConfig


def stream_callback(event_type: str, data: dict):
    if event_type == "node_start":
        sys.stdout.write(f"\n>> starting: {data.get('node', 'unknown')}...")
        sys.stdout.flush()
    elif event_type == "node_end":
        sys.stdout.write(" done")
        sys.stdout.flush()
    elif event_type == "search":
        sys.stdout.write(f"\n   searching: {data.get('query', '')}")
        sys.stdout.flush()
    elif event_type == "iteration":
        sys.stdout.write(f"\n>> iteration {data.get('count', '?')} of {data.get('max', '?')}")
        sys.stdout.flush()


def run_with_streaming(query: str, cfg: AgentConfig):
    from deep_research.agent import build_graph, make_initial_state
    
    graph = build_graph()
    state = make_initial_state(query, cfg)
    
    print(f"query: {query}")
    print("=" * 50)
    
    current_iteration = 0
    
    for event in graph.stream(state, config={"configurable": cfg.to_configurable()}):
        for node_name, node_output in event.items():
            stream_callback("node_start", {"node": node_name})
            
            if node_name == "plan_searches":
                new_iter = node_output.get("iteration", 0)
                if new_iter > current_iteration:
                    current_iteration = new_iter
                    stream_callback("iteration", {"count": current_iteration, "max": cfg.max_iterations})
            
            if node_name == "execute_searches":
                for sq in node_output.get("search_results", []):
                    stream_callback("search", {"query": sq.get("query", "")})
            
            stream_callback("node_end", {"node": node_name})
            
            if node_name == "synthesize_report":
                print("\n" + "=" * 50)
                print(node_output.get("report", ""))
                return node_output
    
    return state


def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="?", default="latest trends in renewable energy storage")
    parser.add_argument("--max-iterations", type=int, default=3)
    parser.add_argument("--max-searches", type=int, default=5)
    parser.add_argument("--model", type=str, default="gpt-4o")
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--report-style", type=str, default="detailed")
    parser.add_argument("--search-provider", type=str, default="tavily", choices=["tavily", "exa", "serpapi"])
    parser.add_argument("--stream", action="store_true", help="enable streaming output")
    args = parser.parse_args()
    
    cfg = AgentConfig(
        max_iterations=args.max_iterations,
        max_searches_per_iteration=args.max_searches,
        model=args.model,
        temperature=args.temperature,
        report_style=args.report_style,
        search_provider=args.search_provider,
        streaming=args.stream,
    )
    
    if args.stream:
        run_with_streaming(args.query, cfg)
    else:
        result = run_research(args.query, cfg)
        report = result.get("report") or ""
        print(report)


if __name__ == "__main__":
    main()
