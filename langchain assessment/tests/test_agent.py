import unittest
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage, HumanMessage
from deep_research import run_research, AgentConfig


class FakeLLM:
    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0

    def invoke(self, prompt):
        if not self.responses:
            return AIMessage(content="")
        self.call_count += 1
        return AIMessage(content=self.responses.pop(0))


def fake_search_success(*args, **kwargs):
    return {
        "results": [
            {"title": "Test Source", "url": "https://example.com", "content": "test content about the topic"}
        ],
        "error": None,
    }


def fake_search_empty(*args, **kwargs):
    return {"results": [], "error": None}


def fake_search_error(*args, **kwargs):
    return {"results": [], "error": "api_timeout"}


def fake_llm_factory(responses):
    def _factory(*args, **kwargs):
        return FakeLLM(list(responses))
    return _factory


class TestBasicFlow(unittest.TestCase):
    def test_successful_research(self):
        responses = [
            '{"query_type":"evergreen","sub_questions":["q1","q2","q3"],"scope_note":null,"needs_recent_data":false}',
            '["search query one","search query two"]',
            '{"is_sufficient": true, "gaps": []}',
            "# Test Report\n\n## executive summary\nfindings here [1]\n\n## key findings\n\n### finding one\ndetails [1]\n\n## conflicting data and uncertainties\nnone\n\n## limitations\n- none\n\n## sources\n[1] Test Source - https://example.com",
        ]
        cfg = AgentConfig(max_iterations=1, max_searches_per_iteration=2)
        factory = fake_llm_factory(responses)
        with patch("deep_research.nodes.analyzer.ChatOpenAI", new=factory), \
             patch("deep_research.nodes.planner.ChatOpenAI", new=factory), \
             patch("deep_research.nodes.evaluator.ChatOpenAI", new=factory), \
             patch("deep_research.nodes.writer.ChatOpenAI", new=factory), \
             patch("deep_research.nodes.searcher.run_search", new=fake_search_success):
            result = run_research("test query", cfg)
        self.assertIn("report", result)
        self.assertTrue(result["report"].startswith("#"))
        self.assertEqual(result["messages"][-1].content, result["report"])


class TestEmptyResults(unittest.TestCase):
    def test_no_search_results(self):
        responses = [
            '{"query_type":"evergreen","sub_questions":["q1","q2"],"scope_note":null,"needs_recent_data":false}',
            '["search one","search two"]',
            '{"is_sufficient": false, "gaps": ["no data found"]}',
            '["retry search one"]',
            '{"is_sufficient": true, "gaps": []}',
            "# Report\n\n## executive summary\nno sources\n\n## key findings\n\n### none\nno data\n\n## conflicting data and uncertainties\nno data\n\n## limitations\n- no sources\n\n## sources\nnone",
        ]
        cfg = AgentConfig(max_iterations=2, max_searches_per_iteration=2)
        factory = fake_llm_factory(responses)
        with patch("deep_research.nodes.analyzer.ChatOpenAI", new=factory), \
             patch("deep_research.nodes.planner.ChatOpenAI", new=factory), \
             patch("deep_research.nodes.evaluator.ChatOpenAI", new=factory), \
             patch("deep_research.nodes.writer.ChatOpenAI", new=factory), \
             patch("deep_research.nodes.searcher.run_search", new=fake_search_empty):
            result = run_research("obscure topic", cfg)
        self.assertIn("report", result)
        self.assertEqual(len(result["sources"]), 0)


class TestAPIFailure(unittest.TestCase):
    def test_search_api_error(self):
        responses = [
            '{"query_type":"evergreen","sub_questions":["q1"],"scope_note":null,"needs_recent_data":false}',
            '["failing query"]',
            '{"is_sufficient": true, "gaps": []}',
            "# Report\n\n## executive summary\nsearch failed\n\n## key findings\n\n### none\nno data due to api error\n\n## conflicting data and uncertainties\nno data\n\n## limitations\n- api failure\n\n## sources\nnone",
        ]
        cfg = AgentConfig(max_iterations=1, max_searches_per_iteration=1)
        factory = fake_llm_factory(responses)
        with patch("deep_research.nodes.analyzer.ChatOpenAI", new=factory), \
             patch("deep_research.nodes.planner.ChatOpenAI", new=factory), \
             patch("deep_research.nodes.evaluator.ChatOpenAI", new=factory), \
             patch("deep_research.nodes.writer.ChatOpenAI", new=factory), \
             patch("deep_research.nodes.searcher.run_search", new=fake_search_error):
            result = run_research("test query", cfg)
        self.assertIn("report", result)
        self.assertTrue(any("api_timeout" in g or "error" in g.lower() for g in result.get("gaps", [])))


class TestMultiIteration(unittest.TestCase):
    def test_loops_when_gaps_found(self):
        call_counter = {"plan": 0, "eval": 0}
        
        def counting_plan_factory(*args, **kwargs):
            class CountingLLM:
                def invoke(self, prompt):
                    call_counter["plan"] += 1
                    return AIMessage(content='["query iteration ' + str(call_counter["plan"]) + '"]')
            return CountingLLM()
        
        def counting_eval_factory(*args, **kwargs):
            class CountingLLM:
                def invoke(self, prompt):
                    call_counter["eval"] += 1
                    if call_counter["eval"] < 3:
                        return AIMessage(content='{"is_sufficient": false, "gaps": ["need more data"]}')
                    return AIMessage(content='{"is_sufficient": true, "gaps": []}')
            return CountingLLM()
        
        analyze_responses = ['{"query_type":"evergreen","sub_questions":["q1","q2"],"scope_note":null,"needs_recent_data":false}']
        write_responses = ["# Final Report\n\n## executive summary\ndone\n\n## key findings\n\n### finding\ndata [1]\n\n## conflicting data and uncertainties\nnone\n\n## limitations\n- none\n\n## sources\n[1] Source - https://example.com"]
        
        cfg = AgentConfig(max_iterations=5, max_searches_per_iteration=2)
        
        with patch("deep_research.nodes.analyzer.ChatOpenAI", new=fake_llm_factory(analyze_responses)), \
             patch("deep_research.nodes.planner.ChatOpenAI", new=counting_plan_factory), \
             patch("deep_research.nodes.evaluator.ChatOpenAI", new=counting_eval_factory), \
             patch("deep_research.nodes.writer.ChatOpenAI", new=fake_llm_factory(write_responses)), \
             patch("deep_research.nodes.searcher.run_search", new=fake_search_success):
            result = run_research("complex topic", cfg)
        
        self.assertEqual(call_counter["plan"], 3)
        self.assertEqual(call_counter["eval"], 3)
        self.assertIn("report", result)


class TestAmbiguousQuery(unittest.TestCase):
    def test_ambiguous_query_adds_scope_note(self):
        responses = [
            '{"query_type":"ambiguous","sub_questions":["q1","q2"],"scope_note":"assuming user means the planet mercury, not the element","needs_recent_data":false}',
            '["mercury planet facts"]',
            '{"is_sufficient": true, "gaps": []}',
            "# Mercury Overview\n\n## executive summary\ninfo about mercury [1]\n\n## key findings\n\n### finding\nplanet data [1]\n\n## conflicting data and uncertainties\nnone\n\n## limitations\n- assumed planet not element\n\n## sources\n[1] Source - https://example.com",
        ]
        cfg = AgentConfig(max_iterations=1, max_searches_per_iteration=2)
        factory = fake_llm_factory(responses)
        with patch("deep_research.nodes.analyzer.ChatOpenAI", new=factory), \
             patch("deep_research.nodes.planner.ChatOpenAI", new=factory), \
             patch("deep_research.nodes.evaluator.ChatOpenAI", new=factory), \
             patch("deep_research.nodes.writer.ChatOpenAI", new=factory), \
             patch("deep_research.nodes.searcher.run_search", new=fake_search_success):
            result = run_research("tell me about mercury", cfg)
        self.assertIn("report", result)
        self.assertTrue(any("planet" in g or "mercury" in g.lower() for g in result.get("gaps", [])))


class TestMaxIterationsCap(unittest.TestCase):
    def test_stops_at_max_iterations(self):
        eval_calls = {"count": 0}
        
        def never_sufficient_eval(*args, **kwargs):
            class NeverSufficientLLM:
                def invoke(self, prompt):
                    eval_calls["count"] += 1
                    return AIMessage(content='{"is_sufficient": false, "gaps": ["always need more"]}')
            return NeverSufficientLLM()
        
        analyze_responses = ['{"query_type":"evergreen","sub_questions":["q1"],"scope_note":null,"needs_recent_data":false}']
        plan_responses = ['["query 1"]', '["query 2"]', '["query 3"]', '["query 4"]', '["query 5"]']
        write_responses = ["# Report\n\n## executive summary\nforced stop\n\n## key findings\n\n### finding\ndata\n\n## conflicting data and uncertainties\nmax iterations reached\n\n## limitations\n- stopped at max iterations\n\n## sources\nnone"]
        
        cfg = AgentConfig(max_iterations=3, max_searches_per_iteration=1)
        
        with patch("deep_research.nodes.analyzer.ChatOpenAI", new=fake_llm_factory(analyze_responses)), \
             patch("deep_research.nodes.planner.ChatOpenAI", new=fake_llm_factory(plan_responses)), \
             patch("deep_research.nodes.evaluator.ChatOpenAI", new=never_sufficient_eval), \
             patch("deep_research.nodes.writer.ChatOpenAI", new=fake_llm_factory(write_responses)), \
             patch("deep_research.nodes.searcher.run_search", new=fake_search_success):
            result = run_research("impossible to satisfy", cfg)
        
        self.assertEqual(result["iteration"], 3)
        self.assertIn("report", result)


if __name__ == "__main__":
    unittest.main()