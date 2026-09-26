import pandas as pd

import report
import tools

TICKER = "AAPL"


def test_get_prices_reads_cache():
    df = tools.get_prices(TICKER)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "Close" in df.columns


def test_get_financials_reads_cache():
    df = tools.get_financials(TICKER)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.shape[1] >= 1


def test_get_news_returns_agreed_schema():
    records = tools.get_news(TICKER)
    assert isinstance(records, list)
    assert records
    required = {
        "article_id", "ticker", "source", "url", "published_at",
        "text", "text_type",
    }
    for r in records:
        assert required <= set(r)
        assert r["ticker"] == TICKER
        assert r["text_type"] in {"headline", "summary", "full"}


def test_get_news_article_ids_unique_and_present():
    records = tools.get_news(TICKER)
    ids = [r["article_id"] for r in records]
    assert all(ids)
    assert len(ids) == len(set(ids))


def test_missing_ticker_falls_through_to_live(monkeypatch):
    called = {}

    def fake_history(*a, **k):
        called["hit"] = True
        return pd.DataFrame({"Close": [1.0]})

    monkeypatch.setattr(
        tools, "_live_prices", lambda sym, period: fake_history()
    )
    df = tools.get_prices("ZZZZ")
    assert called.get("hit")
    assert "Close" in df.columns


def test_specialist_result_shape():
    out = report.specialist_result(
        findings=["f1"], source_ids=["a1"], limitations=["small sample"]
    )
    assert out["findings"] == ["f1"]
    assert out["source_ids"] == ["a1"]
    assert out["limitations"] == ["small sample"]
    assert "missing_data" in out and "dates_units" in out


def test_assemble_report_preserves_source_links():
    specialists = {
        "news": report.specialist_result(
            findings=["n"], source_ids=["a1", "a2"]
        ),
        "market": report.specialist_result(
            findings=["m"], source_ids=["p1"]
        ),
    }
    rep = report.assemble_report(specialists)
    assert set(rep["sections"]) == {"news", "market"}
    assert set(rep["all_source_ids"]) == {"a1", "a2", "p1"}


def test_run_news_chain_stub_contract():
    records = tools.get_news(TICKER)
    out = report.run_news_chain(records, llm=None)
    assert set(out) >= {"stages", "claims", "summary", "trace", "status"}
    assert out["status"] == "stub"
