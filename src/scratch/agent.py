"""Investment Research Agent: one ticker end to end.

    uv run python src/scratch/agent.py AAPL
"""

import sys

import memory
import planner
import review
import router
from report import assemble_report
from specialists import SPECIALISTS


def _empty(result):
    return (result is None or getattr(result, "empty", False)
            or (isinstance(result, list) and not result))


class ResearchAgent:
    def __init__(self, memory_path=memory.MEMORY_PATH):
        self.memory_path = memory_path

    def process(self, symbol):
        symbol = symbol.upper()

        def say(msg):
            print(f"[{symbol}] {msg}", flush=True)

        lessons = memory.load_lessons(symbol, self.memory_path)
        say(f"loaded {len(lessons)} lesson(s)")
        plan = planner.make_plan(symbol, lessons)
        say(f"plan ({plan['source']}): "
            + ", ".join(s["tool"] for s in plan["steps"]))
        executed = planner.execute_plan(plan)

        routed, routes = {r: [] for r in router.ROUTES}, []
        for step in executed:
            if step["error"] or _empty(step["result"]):
                continue
            decision = router.route(step)
            routes.append({"tool": step["tool"], **decision})
            routed[decision["route"]].append(step)
        say("routes: " + ", ".join(
            f"{r['tool']}->{r['route']}" for r in routes))

        sections = {}
        for name, items in routed.items():
            if items:
                say(f"running {name} specialist")
                sections[name] = SPECIALISTS[name](symbol, items)
        assembled = assemble_report(sections)
        evidence = review.evidence_view(assembled)

        say("drafting and reviewing")
        draft = review.draft_report(symbol, evidence, lessons)
        headlines = list(dict.fromkeys(
            r["title"] for s in executed if s["tool"] == "get_news"
            for r in s["result"] or []))
        cycle = review.run_review_cycle(draft, evidence, symbol, plan,
                                        headlines)
        saved = memory.save_lessons(symbol, cycle["lessons"],
                                    self.memory_path)
        say(f"review {cycle['status']} after "
            f"{len(cycle['history'])} draft(s); lessons: {cycle['lessons']}")

        return {
            "symbol": symbol,
            "lessons_loaded": lessons, "plan": plan,
            "tool_calls": executed, "routes": routes,
            "sections": sections, "evidence": evidence, "review": cycle,
            "lessons_saved": cycle["lessons"], "memory_after": saved,
        }


if __name__ == "__main__":
    trace = ResearchAgent().process(sys.argv[1] if len(sys.argv) > 1
                                    else "AAPL")
    print(trace["review"]["final_report"])
