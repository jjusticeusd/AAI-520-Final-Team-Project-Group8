"""Data tools for the research agent (AF2).

Each tool reads a committed cache under ``data/`` and falls through to the live
yfinance API only on a cache miss. yfinance is imported lazily inside the
fallthrough so the cache-hit path needs no network.
"""

from datetime import datetime, timezone
from pathlib import Path

import json

import pandas as pd


def _find_data_dir(start=None):
    start = Path(start or Path.cwd()).resolve()
    for base in [start, *start.parents]:
        candidate = base / "data"
        if candidate.is_dir():
            return candidate
    return Path("data")


DATA_DIR = _find_data_dir()


def _cache_path(data_dir, name):
    return Path(data_dir) / name


def _live_prices(symbol, period):
    import yfinance as yf

    return yf.Ticker(symbol).history(period=period)


def _live_financials(symbol):
    import yfinance as yf

    return yf.Ticker(symbol).quarterly_financials


def _live_news(symbol):
    import yfinance as yf

    return yf.Search(symbol).news


PERIOD_MONTHS = {"1mo": 1, "3mo": 3, "6mo": 6, "1y": 12}


def get_prices(symbol, period="6mo", data_dir=DATA_DIR):
    path = _cache_path(data_dir, f"{symbol}_prices.csv")
    if not path.exists():
        return _live_prices(symbol, period)
    df = pd.read_csv(path, index_col=0)
    # Mixed EDT/EST offsets leave the index as strings unless forced to UTC.
    df.index = pd.to_datetime(df.index, utc=True)
    start = df.index[-1] - pd.DateOffset(months=PERIOD_MONTHS[period])
    return df[df.index >= start]


def get_financials(symbol, data_dir=DATA_DIR):
    path = _cache_path(data_dir, f"{symbol}_financials.csv")
    if path.exists():
        return pd.read_csv(path, index_col=0)
    return _live_financials(symbol)


def _normalize_article(raw, symbol):
    if "uuid" in raw:
        return _normalize_search_article(raw, symbol)
    content = raw.get("content", raw)
    provider = content.get("provider") or {}
    click = content.get("canonicalUrl") or content.get("clickThroughUrl") or {}
    url = click.get("url")
    summary = content.get("summary") or content.get("description") or ""
    title = content.get("title") or ""
    if summary:
        text, text_type = summary, "summary"
    else:
        text, text_type = title, "headline"
    return {
        "article_id": content.get("id") or raw.get("id"),
        "ticker": symbol,
        "source": provider.get("displayName"),
        "url": url,
        "published_at": content.get("pubDate"),
        "retrieved_at": None,
        "title": title,
        "text": text,
        "text_type": text_type,
    }


def _normalize_search_article(raw, symbol):
    published = raw.get("providerPublishTime")
    if published:
        published = datetime.fromtimestamp(published, timezone.utc)
        published = published.isoformat()
    return {
        "article_id": raw["uuid"],
        "ticker": symbol,
        "source": raw.get("publisher"),
        "url": raw.get("link"),
        "published_at": published,
        "retrieved_at": None,
        "title": raw.get("title") or "",
        "text": raw.get("title") or "",
        "text_type": "headline",
    }


def get_news(symbol, data_dir=DATA_DIR):
    path = _cache_path(data_dir, f"{symbol}_news.json")
    if path.exists():
        raw = json.loads(path.read_text())
    else:
        raw = _live_news(symbol)
    records = [_normalize_article(item, symbol) for item in raw]
    if not path.exists():
        now = datetime.now(timezone.utc).isoformat()
        for r in records:
            r["retrieved_at"] = now
    return records


_embedder = None


def rag_query(symbol, query, k=3, data_dir=DATA_DIR):
    global _embedder
    from sentence_transformers import SentenceTransformer

    records = get_news(symbol, data_dir)
    if not records:
        return []
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    docs = [f"{r['title']}. {r['text']}" for r in records]
    vecs = _embedder.encode(docs, normalize_embeddings=True)
    q = _embedder.encode([query], normalize_embeddings=True)[0]
    scores = vecs @ q
    top = scores.argsort()[::-1][:k]
    return [{**records[i], "score": round(float(scores[i]), 3)} for i in top]


TOOLS = {
    "get_prices": {
        "fn": get_prices,
        "args": {"symbol": "ticker", "period": "one of " + ", ".join(
            PERIOD_MONTHS)},
        "description": "Daily price and volume history for trend, "
                       "volatility and drawdown analysis.",
    },
    "get_financials": {
        "fn": get_financials,
        "args": {"symbol": "ticker"},
        "description": "Quarterly income statement: revenue, net income, "
                       "margins, EPS.",
    },
    "get_news": {
        "fn": get_news,
        "args": {"symbol": "ticker"},
        "description": "Recent news articles mentioning the ticker.",
    },
    "rag_query": {
        "fn": rag_query,
        "args": {"symbol": "ticker",
                 "query": "specific question to search the news for"},
        "description": "Semantic search over the ticker's news for one "
                       "specific topic.",
    },
}


def validate_call(name, args, symbol):
    if name not in TOOLS:
        raise ValueError(f"unknown tool {name!r}; choose from {list(TOOLS)}")
    expected = set(TOOLS[name]["args"])
    if not isinstance(args, dict) or set(args) != expected:
        raise ValueError(f"{name} takes exactly these args: "
                         f"{sorted(expected)}")
    if args["symbol"] != symbol:
        raise ValueError(f"{name}: symbol must be {symbol!r}")
    if name == "get_prices" and args["period"] not in PERIOD_MONTHS:
        raise ValueError(f"period must be one of {list(PERIOD_MONTHS)}")
    if name == "rag_query" and not str(args["query"]).strip():
        raise ValueError("rag_query needs a nonempty query")


def call_tool(name, args):
    return TOOLS[name]["fn"](**args)
