"""Earnings, market and news specialists (WP2 targets).

Metrics are computed in pandas; the LLM only narrates the computed numbers.
"""

import pandas as pd

import llm
import news_chain
from report import specialist_result

SYSTEM = (
    "You are a financial analyst. Use only the supplied metrics; do not add "
    "numbers that are not in them. Return one JSON object only."
)
EARNINGS_ROWS = ["Total Revenue", "Gross Profit", "Operating Income",
                 "Net Income", "Diluted EPS"]


def _frames(items):
    return [i["result"] for i in items
            if isinstance(i["result"], pd.DataFrame) and not i["result"].empty]


def pct(new, old):
    return f"{(new - old) / abs(old) * 100:.1f}%" if old else None


def money(x):
    return f"${x / 1e9:.2f}B" if abs(x) >= 1e8 else f"{x:.2f}"


def market_metrics(df):
    close = df["Close"]
    daily = close.pct_change().dropna()
    peak = close.cummax()
    metrics = {
        "start": str(close.index[0].date()),
        "end": str(close.index[-1].date()),
        "last_close": f"{close.iloc[-1]:.2f}",
        "period_return": pct(close.iloc[-1], close.iloc[0]),
        "annualized_volatility": f"{daily.std() * 252 ** 0.5 * 100:.1f}%",
        "max_drawdown": f"{((close - peak) / peak).min() * 100:.1f}%",
    }
    for n in (50, 200):
        if len(close) >= n:
            metrics[f"ma{n}"] = f"{close.rolling(n).mean().iloc[-1]:.2f}"
    return metrics


def earnings_metrics(df):
    df = df[sorted(df.columns, reverse=True)]
    latest = df.columns[0]
    metrics = {"latest_quarter": str(latest)[:10]}
    for row in EARNINGS_ROWS:
        if row not in df.index or pd.isna(df.at[row, latest]):
            continue
        s = df.loc[row].dropna()
        metrics[row] = money(s.iloc[0])
        if len(s) > 1:
            metrics[f"{row} QoQ"] = pct(s.iloc[0], s.iloc[1])
        if len(s) > 4:
            metrics[f"{row} YoY"] = pct(s.iloc[0], s.iloc[4])
    rev = df.at["Total Revenue", latest] if "Total Revenue" in df.index else 0
    for row in ("Gross Profit", "Operating Income", "Net Income"):
        if rev and row in df.index and pd.notna(df.at[row, latest]):
            metrics[f"{row} margin"] = f"{df.at[row, latest] / rev * 100:.1f}%"
    return metrics


def narrate(kind, symbol, metrics):
    prompt = (
        f"Write 2 to 4 short {kind} findings for {symbol} from these "
        f"metrics. Quote numbers exactly as given.\nMETRICS: {metrics}\n"
        'Return {"findings": ["...", "..."]}'
    )

    def check(obj):
        if not obj["findings"] or not all(
                isinstance(f, str) for f in obj["findings"]):
            raise ValueError("findings must be a nonempty list of strings")

    try:
        return llm.llm_json(prompt, SYSTEM, 250, validate=check)["findings"]
    except ValueError:
        return [f"{k}: {v}" for k, v in metrics.items()]


def market_specialist(symbol, items):
    frames = [f for f in _frames(items) if "Close" in f.columns]
    if not frames:
        return specialist_result([], [], missing_data=["no price history"])
    df = max(frames, key=len)
    metrics = market_metrics(df)
    out = specialist_result(
        narrate("market", symbol, metrics), [f"{symbol}:prices"],
        dates_units=[f"{metrics['start']} to {metrics['end']}, USD"],
        limitations=["Past price behaviour does not predict returns."])
    out["metrics"] = metrics
    return out


def earnings_specialist(symbol, items):
    frames = [f for f in _frames(items) if "Total Revenue" in f.index]
    if not frames:
        return specialist_result([], [], missing_data=["no financials"])
    metrics = earnings_metrics(frames[0])
    out = specialist_result(
        narrate("earnings", symbol, metrics), [f"{symbol}:financials"],
        dates_units=[f"quarter ending {metrics['latest_quarter']}, USD"],
        limitations=["Quarterly income statement only; no balance sheet."])
    out["metrics"] = metrics
    return out


def news_specialist(symbol, items):
    records = {}
    for i in items:
        for r in i["result"] or []:
            if isinstance(r, dict) and r.get("article_id"):
                records.setdefault(r["article_id"], r)
    chain = news_chain.run_chain(symbol, list(records.values()))
    summary = chain["stages"]["summarize"]
    cited = {c["claim_id"]: c["article_id"] for c in chain["claims"]}
    findings = [b["text"] for b in summary["bullets"]] if summary else []
    sources = list(dict.fromkeys(
        cited[i] for b in (summary or {}).get("bullets", [])
        for i in b["claim_ids"]))
    irrelevant = sum(not c["relevant"] for c in chain["stages"]["classify"])
    out = specialist_result(
        findings, sources,
        missing_data=[] if findings else ["no relevant news claims"],
        limitations=[
            "Yahoo news items are summaries or headlines, not full articles.",
            f"{irrelevant} of {len(chain['stages']['classify'])} articles "
            "were classified as not about the company.",
        ] + chain["errors"])
    out["chain"] = chain
    return out


SPECIALISTS = {"market": market_specialist,
               "earnings": earnings_specialist,
               "news": news_specialist}
