"""LLM research planner (AF1) that chooses tools and arguments (AF2)."""

import llm
import tools

SYSTEM = (
    "You are an investment research planner. Return one JSON object only, "
    "no prose."
)
MAX_STEPS = 6


def fallback_plan(symbol):
    return [
        {"tool": "get_prices", "args": {"symbol": symbol, "period": "6mo"},
         "reason": "fallback"},
        {"tool": "get_financials", "args": {"symbol": symbol},
         "reason": "fallback"},
        {"tool": "get_news", "args": {"symbol": symbol},
         "reason": "fallback"},
    ]


def plan_prompt(symbol, lessons):
    catalog = "\n".join(
        f"- {name}: {spec['description']} Args: "
        + ", ".join(f"{a} ({d})" for a, d in spec["args"].items())
        for name, spec in tools.TOOLS.items()
    )
    cached = (tools.DATA_DIR / f"{symbol}_prices.csv").exists()
    notes = "\n".join(f"- {n}" for n in lessons) or "- none yet"
    return (
        f"Plan the research steps for stock {symbol}.\n"
        f"Tools:\n{catalog}\n"
        f"Local cached data for {symbol}: "
        f"{'yes' if cached else 'no, tools will call the live API'}.\n"
        f"Lessons from earlier runs on {symbol} (apply them):\n{notes}\n"
        'Return {"steps": [{"tool": "...", "args": {...}, "reason": "..."}]} '
        f"with 3 to {MAX_STEPS} steps. Keep each reason under 15 words. "
        "Pass exactly the listed args. "
        "Pick the price period that fits the question. Use rag_query with a "
        f"specific question about {symbol} when a topic needs targeted news."
    )


def validate_plan(obj, symbol):
    steps = obj["steps"]
    if not isinstance(steps, list) or not 1 <= len(steps) <= MAX_STEPS:
        raise ValueError(f"steps must be a list of 1-{MAX_STEPS} items")
    for step in steps:
        tools.validate_call(step["tool"], step["args"], symbol)


def make_plan(symbol, lessons):
    prompt = plan_prompt(symbol, lessons)
    try:
        obj = llm.llm_json(prompt, SYSTEM, 700,
                           validate=lambda o: validate_plan(o, symbol))
        return {"source": "llm", "prompt": prompt, "steps": obj["steps"]}
    except ValueError as e:
        return {"source": "fallback", "prompt": prompt, "error": str(e),
                "steps": fallback_plan(symbol)}


def execute_plan(plan):
    executed = []
    for step in plan["steps"]:
        try:
            result, error = tools.call_tool(step["tool"], step["args"]), None
        except Exception as e:
            result, error = None, f"{type(e).__name__}: {e}"
        executed.append({**step, "result": result, "error": error})
    return executed
