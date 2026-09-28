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
