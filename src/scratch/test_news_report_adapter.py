"""Offline adapter tests. Synthetic fixtures do not represent real news."""
from copy import deepcopy
import unittest

from news_report_adapter import news_result_to_specialist
from report import assemble_report, specialist_result


def fixture():
    return {
        'status': 'needs_manual_review',
        'claims': [{
            'claim_id': 'TEST_C1', 'article_id': 'TEST_A1',
            'statement': 'Synthetic company reported 5 units.',
            'evidence_quote': 'Synthetic company reported 5 units.',
            'url': 'https://example.org/test', 'source': 'Synthetic fixture',
            'published_at': None, 'updated_at': '2026-01-01',
            'text_type': 'summary', 'support_review': 'pending',
        }],
        'stages': {'summarize': {
            'bullets': [{
                'text': 'Synthetic company reported 5 units.',
                'claim_ids': ['TEST_C1'],
                'source_urls': ['https://example.org/test'],
            }],
            'limitations': ['Synthetic data; not factual evidence.'],
        }},
    }


class AdapterTests(unittest.TestCase):
    def test_preserves_contract_evidence_and_input(self):
        chain = fixture()
        original = deepcopy(chain)
        result = news_result_to_specialist(chain)
        self.assertEqual(set(result), {
            'findings', 'source_ids', 'dates_units',
            'missing_data', 'limitations',
        })
        self.assertEqual(result['findings'][0]['evidence'], chain['claims'])
        self.assertEqual(result['source_ids'], ['TEST_A1'])
        self.assertIn(chain['stages']['summarize']['limitations'][0],
                      result['limitations'])
        result['findings'][0]['evidence'][0]['statement'] = 'Changed copy'
        self.assertEqual(chain, original)

    def test_update_date_is_not_event_date(self):
        result = news_result_to_specialist(fixture())
        self.assertEqual(result['dates_units'][0]['kind'], 'updated_at')
        self.assertFalse(result['dates_units'][0]['is_event_date'])
        self.assertIsNone(result['dates_units'][0]['unit'])
        self.assertTrue(any('publication date' in x
                            for x in result['missing_data']))

    def test_unknown_citation_rejected(self):
        chain = fixture()
        chain['stages']['summarize']['bullets'][0]['claim_ids'] = ['BAD']
        with self.assertRaisesRegex(ValueError, 'Unknown claim'):
            news_result_to_specialist(chain)

    def test_conflicting_url_rejected(self):
        chain = fixture()
        chain['stages']['summarize']['bullets'][0]['source_urls'] = ['bad']
        with self.assertRaisesRegex(ValueError, 'URLs disagree'):
            news_result_to_specialist(chain)

    def test_missing_summary_rejected(self):
        chain = fixture()
        chain['stages']['summarize'] = None
        with self.assertRaisesRegex(ValueError, 'No structured summary'):
            news_result_to_specialist(chain)

    def test_assembly_with_synthetic_market_sections(self):
        news = news_result_to_specialist(fixture())
        mock = specialist_result(
            findings=['SYNTHETIC interface fixture; not market analysis.'],
            source_ids=['SYNTHETIC_MARKET'],
            limitations=['No real price or financial analysis tested.'],
        )
        report = assemble_report({'news': news, 'prices': mock})
        self.assertEqual(report['sections']['news'], news)
        self.assertEqual(report['all_source_ids'],
                         ['TEST_A1', 'SYNTHETIC_MARKET'])
        self.assertIn(news['limitations'][0], report['limitations'])
        self.assertEqual(report['missing_data'], news['missing_data'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
