"""Offline integration checks with explicitly synthetic model responses.

Run: python src/scratch/test_news_pipeline.py
No model, GPU, external data, or network is required. These checks verify
software behavior, not the factual quality of a model's generated analysis.
"""

from contextlib import ExitStack
from copy import deepcopy
import json
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

if __package__:
    from . import news_pipeline as news
    from . import report
else:
    import news_pipeline as news
    import report


def article(article_id='fixture-1'):
    return {
        'article_id': article_id,
        'ticker': 'TEST',
        'title': 'Synthetic company announcement',
        'source': 'Synthetic fixture',
        'url': 'https://example.org/news/1',
        'published_at': '2026-01-01T00:00:00+00:00',
        'retrieved_at': None,
        'text': '<p>Example Co reported $5 million, not $6 million.</p>',
        'text_type': 'summary',
    }


def classification(relevant=True):
    return {
        'category': 'earnings', 'relevant': relevant,
        'reason': 'Synthetic test response.',
    }


def replies(article_id='fixture-1'):
    return [
        classification(),
        {'claims': [{
            'statement': 'Example Co reported $5 million.',
            'evidence_id': 'E1',
        }]},
        {
            'bullets': [{
                'text': 'Example Co reported $5 million.',
                'claim_ids': [article_id + '_C1'],
            }],
            'limitations': ['Synthetic fixture; not real financial news.'],
        },
    ]


class ScriptedLLM:
    def __init__(self, outputs, fenced=False):
        self.outputs = list(outputs)
        self.prompts = []
        self.fenced = fenced

    def __call__(self, prompt, **kwargs):
        self.prompts.append(prompt)
        value = self.outputs.pop(0)
        raw = value if isinstance(value, str) else json.dumps(value)
        return '```json\n' + raw + '\n```' if self.fenced else raw


class NewsPipelineTests(unittest.TestCase):
    def test_report_delegates_and_preserves_contract_and_source_ids(self):
        row = article()
        original = deepcopy(row)
        result = report.run_news_chain([row], llm=ScriptedLLM(replies()))
        self.assertEqual(result['status'], 'needs_manual_review')
        self.assertEqual(set(result['stages']), {
            'ingest', 'preprocess', 'classify', 'extract', 'summarize',
        })
        self.assertIsInstance(result['summary'], str)
        claim = result['claims'][0]
        self.assertEqual(claim['article_id'], 'fixture-1')
        self.assertEqual(claim['claim_id'], 'fixture-1_C1')
        self.assertEqual(claim['evidence_quote'],
                         'Example Co reported $5 million, not $6 million.')
        self.assertEqual(row, original)
        self.assertIsNone(result['preprocessed'][0]['retrieved_at'])

    def test_markdown_fence_audit_is_not_mislabeled_as_strict_json(self):
        result = report.run_news_chain(
            [article()], llm=ScriptedLLM(replies(), fenced=True)
        )
        self.assertEqual(len(result['trace']), 3)
        for step in result['trace']:
            self.assertFalse(step['strict_json_valid'])
            self.assertTrue(step['fence_removed'])
            self.assertTrue(step['schema_valid'])
        raw_bullet = result['trace'][-1]['parsed']['bullets'][0]
        output_bullet = result['stages']['summarize']['bullets'][0]
        self.assertNotIn('source_urls', raw_bullet)
        self.assertEqual(output_bullet['source_urls'], [article()['url']])

    def test_empty_and_invalid_input_do_not_load_model(self):
        with patch.object(news, '_shared_news_llm') as model:
            self.assertEqual(report.run_news_chain([])['status'], 'no_data')
            invalid = report.run_news_chain([{'article_id': 'bad'}])
            self.assertEqual(invalid['status'], 'needs_review')
            self.assertEqual(len(invalid['excluded_inputs']), 1)
            model.assert_not_called()

    def test_cleaning_preserves_case_negation_numbers_and_units(self):
        text = (
            '<p>AAPL did NOT grow 12.5%: $1.2 billion.</p>'
            '<script>x()</script>'
        )
        self.assertEqual(
            news.clean_news_text(text),
            'AAPL did NOT grow 12.5%: $1.2 billion.',
        )

    def test_duplicate_urls_and_duplicate_ids_are_excluded(self):
        first = article()
        second = article('fixture-2')
        second['url'] += '#fragment'
        third = article()
        third['url'] += '/different'
        third['text'] = 'A distinct synthetic text.'
        kept, excluded = news.prepare_news([first, second, third])
        self.assertEqual(len(kept), 1)
        self.assertEqual(len(excluded), 2)

    def test_legacy_snapshot_id_is_retained(self):
        row = article()
        row['news_id'] = row.pop('article_id')
        kept, _ = news.prepare_news([row])
        self.assertEqual(kept[0]['article_id'], 'fixture-1')
        self.assertEqual(kept[0]['news_id'], 'fixture-1')

    def test_invalid_classification_stops_that_article(self):
        model = ScriptedLLM(['not JSON'])
        result = report.run_news_chain([article()], llm=model)
        self.assertEqual(result['status'], 'needs_review')
        self.assertEqual(len(model.prompts), 1)
        self.assertEqual(result['claims'], [])
        self.assertEqual(
            result['article_results'][0]['status'], 'classification_failed'
        )

    def test_irrelevant_article_does_not_trigger_extraction(self):
        model = ScriptedLLM([classification(relevant=False)])
        result = report.run_news_chain([article()], llm=model)
        self.assertEqual(result['status'], 'no_relevant_news')
        self.assertEqual(len(model.prompts), 1)
        self.assertEqual(result['summary'], '')

    def test_headline_only_is_not_treated_as_full_evidence(self):
        row = article()
        row['text_type'] = 'headline'
        row['text'] = row['title']
        result = report.run_news_chain(
            [row], llm=ScriptedLLM([classification()])
        )
        self.assertEqual(result['claims'], [])
        self.assertEqual(result['article_results'][0]['status'],
                         'insufficient_evidence_headline_only')

    def test_unknown_summary_citation_fails_validation(self):
        outputs = replies()
        outputs[-1]['bullets'][0]['claim_ids'] = ['nonexistent_C1']
        result = report.run_news_chain(
            [article()], llm=ScriptedLLM(outputs)
        )
        self.assertEqual(result['status'], 'needs_review')
        self.assertEqual(result['summary'], '')
        self.assertIn('unknown claim ID', result['trace'][-1]['error'])

    def test_model_error_is_recorded(self):
        def broken_model(prompt, **kwargs):
            raise RuntimeError('Synthetic model failure')

        result = report.run_news_chain([article()], llm=broken_model)
        self.assertEqual(result['status'], 'needs_review')
        self.assertIn('Synthetic model failure', result['trace'][0]['error'])

    def test_mixed_tickers_are_rejected_before_generation(self):
        second = article('fixture-2')
        second.update({
            'ticker': 'OTHER', 'url': 'https://example.org/news/2',
            'text': 'Another synthetic company announcement.',
        })
        with patch.object(news, '_shared_news_llm') as model:
            with self.assertRaisesRegex(ValueError, 'one ticker'):
                report.run_news_chain([article(), second])
            model.assert_not_called()

    def test_strict_parser_rejects_duplicate_keys_and_nonfinite_numbers(self):
        for raw in ('{"x": 1, "x": 2}', '{"x": NaN}'):
            with self.assertRaises(ValueError):
                news.strict_json(raw)

    def test_injected_helper_receives_settings_for_every_stage(self):
        scripted = ScriptedLLM(replies())
        calls = []

        def helper(prompt, max_new_tokens=512, temperature=0.7,
                   system=None):
            calls.append((max_new_tokens, temperature, system))
            return scripted(prompt)

        result = report.run_news_chain([article()], llm=helper)
        self.assertEqual(result['status'], 'needs_manual_review')
        self.assertEqual(calls, [(700, 0, news.SYSTEM_PROMPT)] * 3)
        self.assertEqual([x['stage'] for x in result['trace']],
                         ['classify', 'extract', 'summarize'])
        for step in result['trace']:
            self.assertEqual(step['generation_settings']['temperature'], 0)

    def test_shared_helper_settings_and_context_guard_without_model(self):
        calls = []
        backend = SimpleNamespace(
            _load=lambda: None,
            _tokenizer=SimpleNamespace(
                apply_chat_template=lambda *args, **kwargs: [1, 2, 3]
            ),
            _model=SimpleNamespace(config=SimpleNamespace(
                max_position_embeddings=4096
            )),
            llm=lambda prompt, **kwargs: calls.append(kwargs) or '{}',
        )
        module_name = news.__package__ + '.llm' if news.__package__ else 'llm'
        with ExitStack() as patches:
            patches.enter_context(patch.dict(
                'sys.modules', {module_name: backend}
            ))
            if news.__package__:
                patches.enter_context(patch.object(
                    sys.modules[news.__package__], 'llm', backend, create=True
                ))
            self.assertEqual(news._shared_news_llm('fixture'), '{}')
            self.assertEqual(calls[0]['temperature'], 0)
            self.assertEqual(calls[0]['max_new_tokens'], 700)
            backend._model.config.max_position_embeddings = 702
            with self.assertRaisesRegex(ValueError, 'context window'):
                news._shared_news_llm('fixture')
            self.assertEqual(len(calls), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
