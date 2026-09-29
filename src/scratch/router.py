"""Route gathered content to the right specialist (WP2)."""

import json

import pandas as pd

import llm

ROUTES = ("earnings", "news", "market")
SYSTEM = "You route financial content to a specialist. Return JSON only."
RULES = {"get_prices": "market", "get_financials": "earnings",
         "get_news": "news", "rag_query": "news"}


def preview(result):
    if isinstance(result, pd.DataFrame):
        return (f"Table {result.shape}. Columns: {list(result.columns)[:8]}. "
                f"Row labels: {list(result.index)[:8]}")
    if isinstance(result, list) and result:
        first = {k: result[0].get(k) for k in ("title", "text")}
        return f"{len(result)} records. First: {json.dumps(first)[:400]}"
    return repr(result)[:200]


def route(step):
    rule = RULES[step["tool"]]
    prompt = (
        "Which specialist should analyze this content?\n"
        "Specialists:\n"
        "- earnings: financial statement table whose rows are line items "
        "such as Total Revenue, Net Income, EPS\n"
        "- news: news articles and headlines\n"
        "- market: daily trading table with Open, High, Low, Close, Volume "
        "columns\n"
        f"CONTENT: {preview(step['result'])}\n"
        'Answer like {"route": "news", "reason": "one short sentence"}. '
        "route must be exactly earnings, news or market."
    )

    def check(obj):
        if obj["route"] not in ROUTES:
            raise ValueError(f"route must be one of {ROUTES}")

    try:
        obj = llm.llm_json(prompt, SYSTEM, 150, validate=check)
        decision = {"route": obj["route"], "reason": obj.get("reason"),
                    "source": "llm"}
    except ValueError as e:
        decision = {"route": rule, "reason": str(e), "source": "rule"}
    decision["agrees_with_rule"] = decision["route"] == rule
    return decision
