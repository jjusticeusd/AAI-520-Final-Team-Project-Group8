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
    if __package__:
        from .news_pipeline import run_news_chain as run_pipeline
    else:
        from news_pipeline import run_news_chain as run_pipeline
    return run_pipeline(records, llm=llm)

