import json

import pytest

import llm
import memory
import news_chain
import planner
import review
import router
import tools

ARTICLE = {"article_id": "abcdefgh-1", "ticker": "AAPL", "source": "X",
           "url": "https://x.test/a", "published_at": None,
           "title": "Apple <b>sales</b>",
           "text": "Apple sales rose 5% in the quarter. Shares moved."}


def script(monkeypatch, *replies):
    queue = list(replies)
    monkeypatch.setattr(
        llm, "llm", lambda prompt, **kw: queue.pop(0))
    return queue


def test_parse_json_ignores_surrounding_prose():
    assert llm.parse_json('Sure: {"a": [1]} done') == {"a": [1]}


def test_llm_json_retries_then_raises(monkeypatch):
    script(monkeypatch, "nope", "still nope")
    with pytest.raises(ValueError):
        llm.llm_json("p", "s")


def test_llm_json_recovers_on_retry(monkeypatch):
    script(monkeypatch, "nope", '{"ok": true}')
    assert llm.llm_json("p", "s") == {"ok": True}


def test_validate_call_rejects_bad_args():
    tools.validate_call("get_prices", {"symbol": "AAPL", "period": "1y"},
                        "AAPL")
    for name, args in [("get_prices", {"symbol": "AAPL", "period": "9y"}),
                       ("get_news", {"symbol": "MSFT"}),
                       ("get_news", {"symbol": "AAPL", "x": 1}),
                       ("launch_missiles", {"symbol": "AAPL"})]:
        with pytest.raises(ValueError):
            tools.validate_call(name, args, "AAPL")


def test_planner_accepts_valid_plan(monkeypatch):
    steps = [{"tool": "rag_query",
              "args": {"symbol": "AAPL", "query": "iPhone demand"},
              "reason": "r"}]
    script(monkeypatch, json.dumps({"steps": steps}))
    plan = planner.make_plan("AAPL", ["check iPhone demand"])
    assert plan["source"] == "llm"
    assert plan["steps"] == steps
    assert "check iPhone demand" in plan["prompt"]


def test_planner_falls_back_on_invalid_plan(monkeypatch):
    bad = json.dumps({"steps": [{"tool": "nope", "args": {}}]})
    script(monkeypatch, bad, bad)
    plan = planner.make_plan("AAPL", [])
    assert plan["source"] == "fallback"
    assert "unknown tool" in plan["error"]


def test_router_uses_rule_when_llm_output_invalid(monkeypatch):
    script(monkeypatch, '{"route": "sports"}', '{"route": "sports"}')
    decision = router.route({"tool": "get_news", "result": [ARTICLE]})
    assert decision["route"] == "news"
    assert decision["source"] == "rule"


def test_memory_round_trip(tmp_path):
    path = tmp_path / "memory.json"
    assert memory.load_lessons("AAPL", path) == []
    memory.save_lessons("AAPL", ["a", "b"], path)
    memory.save_lessons("AAPL", ["b", "c"], path)
    assert memory.load_lessons("AAPL", path) == ["a", "b", "c"]
    assert memory.load_lessons("MSFT", path) == []


def test_news_chain_passes_stage_outputs_and_drops_unquoted_claims(
        monkeypatch):
    queue = script(
        monkeypatch,
        '{"relevant": true, "category": "earnings", "sentiment": "positive",'
        ' "reason": "r"}',
        json.dumps({"claims": [
            {"claim": "sales up", "quote": "Apple sales rose 5%"},
            {"claim": "made up", "quote": "Apple doubled profit"}]}),
        '{"bullets": [{"text": "Sales rose.", "claim_ids": ["abcdefgh-C1"]}]}',
    )
    out = news_chain.run_chain("AAPL", [ARTICLE, dict(ARTICLE)])
    assert not queue
    assert len(out["stages"]["preprocess"]) == 1
    assert out["stages"]["preprocess"][0]["title"] == "Apple sales"
    assert [c["claim_id"] for c in out["claims"]] == ["abcdefgh-C1"]
    assert out["stages"]["extract"][0]["rejected"][0]["claim"] == "made up"
    assert out["stages"]["summarize"]["bullets"][0]["text"] == "Sales rose."


def test_unsupported_numbers_flags_invented_figures():
    evidence = json.dumps({"market": {"metrics": {"return": "12.5%",
                                                  "close": "1,234.50"}}})
    draft = "Returned 12.5% to 1234.5 in 2026 over 3 months, EPS 9.99."
    assert review.unsupported_numbers(draft, evidence) == [9.99]


def evaluation(score):
    return json.dumps({"scores": dict.fromkeys(review.CRITERIA, score),
                       "issues": ["vague"], "feedback": "be specific"})


PLAN = {"steps": [{"tool": "get_news", "args": {"symbol": "AAPL"}}]}
GOOD = "\n".join(f"{h}:\ntext" for h in review.HEADINGS)


def test_missing_headings_requires_heading_lines():
    assert review.missing_headings(GOOD) == []
    assert review.missing_headings("The market rose.") == list(
        review.HEADINGS)


def test_review_cycle_refines_until_pass(monkeypatch):
    script(monkeypatch, evaluation(5), GOOD, evaluation(5),
           '{"lessons": ["rag_query: ask about supply chain"]}')
    out = review.run_review_cycle("no headings", "{}", "AAPL", PLAN)
    assert out["status"] == "passed"
    assert out["final_report"] == GOOD
    assert [h["draft_number"] for h in out["history"]] == [1, 2]
    assert out["history"][0]["evaluation"]["missing_headings"]
    assert out["lessons"] == ["rag_query: ask about supply chain"]


def test_review_cycle_stops_at_draft_limit_with_best_draft(monkeypatch):
    script(monkeypatch, evaluation(3), "d2", evaluation(2), "d3",
           evaluation(1), '{"lessons": ["x"]}', '{"lessons": ["y"]}')
    out = review.run_review_cycle(GOOD, "{}", "AAPL", PLAN)
    assert out["status"] == "needs_review"
    assert len(out["history"]) == 3
    assert out["final_report"] == GOOD
    assert out["lessons"] == []


def test_review_cycle_stops_when_revision_is_unchanged(monkeypatch):
    script(monkeypatch, evaluation(2), GOOD, GOOD,
           '{"lessons": ["get_news"]}')
    out = review.run_review_cycle(GOOD, "{}", "AAPL", PLAN)
    assert out["stop_reason"] == "revision made no change"
    assert len(out["history"]) == 1


def test_review_cycle_stops_when_evaluator_fails(monkeypatch):
    script(monkeypatch, "not json", "still not json", '{"lessons": []}',
           '{"lessons": []}')
    out = review.run_review_cycle(GOOD, "{}", "AAPL", PLAN)
    assert out["status"] == "needs_review"
    assert out["stop_reason"].startswith("evaluator failed")
    assert out["final_report"] == GOOD
