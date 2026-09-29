"""Convert news-chain results to the specialist report format."""
from copy import deepcopy

if __package__:
    from .report import specialist_result
else:
    from report import specialist_result


def unique(values):
    return list(dict.fromkeys(values))


def news_result_to_specialist(chain):
    """Preserve summary citations and evidence without approving
    model claims.
    """
    if chain.get('status') not in ('needs_manual_review', 'needs_review'):
        raise ValueError('This adapter requires a saved reviewable news run.')
    summary = chain.get('stages', {}).get('summarize')
    if not isinstance(summary, dict) or not summary.get('bullets'):
        raise ValueError('No structured summary; inspect the original run.')

    claims = {}
    for claim in chain.get('claims', []):
        cid = claim.get('claim_id')
        if not cid or cid in claims:
            raise ValueError('Missing or duplicate claim_id.')
        claims[cid] = claim

    findings, source_ids, dates_units, missing = [], [], [], []
    source_registry = {}
    dated_sources = set()
    for bullet in summary['bullets']:
        ids = bullet.get('claim_ids')
        if not bullet.get('text') or not isinstance(ids, list) or not ids:
            raise ValueError('Each summary finding needs text and claim IDs.')
        evidence, sources = [], {}
        for cid in ids:
            if cid not in claims:
                raise ValueError(f'Unknown claim ID: {cid}')
            claim = claims[cid]
            aid = claim.get('article_id') or claim.get('news_id')
            url = claim.get('url')
            quote = claim.get('evidence_quote')
            if not aid or not url or not quote:
                raise ValueError(
                    f'Missing source identity, URL or quote: {cid}'
                )
            source = {
                'article_id': aid,
                'url': url,
                'source': claim.get('source'),
                'published_at': claim.get('published_at'),
                'updated_at': claim.get('updated_at'),
                'text_type': claim.get('text_type'),
            }
            if aid in source_registry and source_registry[aid] != source:
                raise ValueError(f'Conflicting source metadata: {aid}')
            source_registry[aid] = source
            sources[aid] = deepcopy(source)
            source_ids.append(aid)
            evidence.append(deepcopy(claim))
            if aid not in dated_sources:
                dated_sources.add(aid)
                for field in ('published_at', 'updated_at'):
                    if source[field]:
                        dates_units.append({
                            'article_id': aid,
                            'kind': field,
                            'value': source[field],
                            'unit': None,
                            'is_event_date': False,
                        })
                if not source['published_at']:
                    missing.append(f'{aid}: publication date unavailable.')
                if source['text_type'] != 'full_article':
                    missing.append(
                        f'{aid}: evidence is {source["text_type"]}; '
                        'full article not supplied as evidence.'
                    )
        urls = unique(s['url'] for s in sources.values())
        if 'source_urls' in bullet and set(bullet['source_urls']) != set(urls):
            raise ValueError('Summary URLs disagree with referenced claims.')
        findings.append({
            'text': bullet['text'],
            'claim_ids': list(ids),
            'sources': list(sources.values()),
            'evidence': evidence,
            'review_status': chain['status'],
        })

    missing.append(
        'Structured event dates, reporting periods, metrics, numeric values '
        'and units have not been mapped; do not infer them from prose.'
    )
    for item in chain.get('excluded_inputs', []):
        missing.append(f'Excluded input: {item}')
    for step in chain.get('trace', []):
        if step.get('error'):
            missing.append(
                f'{step.get("stage")}: {step.get("error")}'
            )
    limitations = list(summary.get('limitations', []))
    limitations.extend([
        f'Original news run status: {chain["status"]}.',
        'This adapter maps existing results; it does not verify facts, '
        'correct omissions, or establish that citations support every word.',
        'Publication and update timestamps are source metadata, '
        'not verified event dates.',
    ])
    return specialist_result(
        findings=findings,
        source_ids=unique(source_ids),
        dates_units=dates_units,
        missing_data=unique(missing),
        limitations=unique(limitations),
    )
