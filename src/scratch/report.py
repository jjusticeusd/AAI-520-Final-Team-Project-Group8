"""Report assembly scaffolding (2.10).

Defines the common specialist result structure, a report assembler that
preserves source links across specialists, and the ``run_news_chain`` seam that
Peng's real prompt chain plugs into (schedule L108). Until then it runs as a
labelled stub so the integration path is testable end to end.
"""


def specialist_result(findings, source_ids, dates_units=None,
                      missing_data=None, limitations=None):
    return {
        "findings": list(findings),
        "source_ids": list(source_ids),
        "dates_units": dates_units or [],
        "missing_data": missing_data or [],
        "limitations": limitations or [],
    }


def assemble_report(specialist_results):
    all_source_ids = []
    limitations = []
    missing_data = []
    for result in specialist_results.values():
        for sid in result["source_ids"]:
            if sid not in all_source_ids:
                all_source_ids.append(sid)
        limitations.extend(result["limitations"])
        missing_data.extend(result["missing_data"])
    return {
        "sections": dict(specialist_results),
        "all_source_ids": all_source_ids,
        "limitations": limitations,
        "missing_data": missing_data,
    }


def run_news_chain(records, llm=None):
    """Ingest -> Preprocess -> Classify -> Extract -> Summarize (WP1).

    Stub seam: returns the agreed contract shape so the router and report
    assembler can integrate against it now. Peng's implementation replaces
    this.
    """
    source_ids = [r.get("article_id") for r in records]
    return {
        "stages": {
            "ingest": records,
            "preprocess": None,
            "classify": None,
            "extract": None,
            "summarize": None,
        },
        "claims": [],
        "summary": "",
        "trace": [
            {
                "stage": "ingest",
                "count": len(records),
                "source_ids": source_ids,
            }
        ],
        "status": "stub",
    }
