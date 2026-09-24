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


def get_prices(symbol, period="6mo", data_dir=DATA_DIR):
    path = _cache_path(data_dir, f"{symbol}_prices.csv")
    if path.exists():
        return pd.read_csv(path, index_col=0, parse_dates=True)
    return _live_prices(symbol, period)


def get_financials(symbol, data_dir=DATA_DIR):
    path = _cache_path(data_dir, f"{symbol}_financials.csv")
    if path.exists():
        return pd.read_csv(path, index_col=0)
    return _live_financials(symbol)


def _normalize_article(raw, symbol):
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
