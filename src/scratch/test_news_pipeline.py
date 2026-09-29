"""Offline behavior checks using synthetic responses, without model loading."""


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
        'target_aliases': ['Example Co'],
        'title': 'Synthetic company announcement',
        'source': 'Synthetic fixture',
        'url': 'https://example.org/news/1',
        'published_at': '2026-01-01T00:00:00+00:00',
        'retrieved_at': None,
        'text': '<p>Example Co reported $5 million, not $6 million.</p>',
        'text_type': 'summary',
    }


def classification(relevant=True, evidence=None):
    return {
        'event_type': 'other', 'category': 'other', 'relevant': relevant,
        'reason': 'Synthetic test response.',
        'sentiment': 'neutral' if relevant else 'unknown',
        'sentiment_reason': 'No supported direction for the target company.',
        'relevance_evidence': (
            evidence or 'Example Co reported $5 million, not $6 million.'
        ) if relevant else None,
        'sentiment_evidence': None,
    }


def replies(article_id='fixture-1'):
    return [
        classification(),
        {'claims': [{
            'statement': 'Example Co reported $5 million.',
            'evidence_id': 'E1',
            'supporting_text': ('Example Co reported $5 million, '
                                'not $6 million.'),
            'company': 'Example Co', 'metric': None, 'value': '$5',
            'unit': 'million', 'event_date': None, 'period': None,
        }]},
        {
            'bullets': [{
                'text': 'Example Co reported $5 million.',
                'claim_ids': [article_id + '_C1'],
            }],
            'limitations': ['Synthetic fixture; not real financial news.'],
        },
    ]


CACHE_CASES = [
    {
        'article_id': 'c3b884fd-fca1-39ea-a847-4f977546401b',
        'title': 'Did AI Servers Really Quadruple Dell Stock?',
        'text': (
            'Dell Technologies (DELL) stock has returned 334% over the '
            'past year, against 16% for the S&P 500. The easy explanation'
            ' is AI orders, but it is incomplete. The bigger change is '
            'what happened to the rest of Dell.'
        ),
    },
    {
        'article_id': '0e4b4b61-05d6-363f-904f-92d88c43735a',
        'title': (
            'Snap targets enterprises with Salesforce, Nvidia AI tools '
            'for augmented-reality glasses'
        ),
        'text': (
            'Sept 16 (Reuters) - Snap on Wednesday announced partnerships'
            ' with companies including Salesforce, Nvidia and Amazon Web '
            'Services to integrate workplace tools into its Specs '
            'augmented-reality glasses,'
        ),
    },
    {
        'article_id': '0bbeb01d-27ca-31bf-a84e-e28460eb4341',
        'title': (
            'S&P 500, Nasdaq, Dow Futures Inch Higher As Investors Digest'
            ' First Rate Hike Since 2023 — INTC, GOOGL, AAPL, SKHY, UAL '
            'In Focus'
        ),
        'text': 'The U.S. Fed hiked rates by 25 basis points to 3.75%-4%.',
    },
    {
        'article_id': 'ebf656ea-14f8-3cb6-8ed4-56e40670652f',
        'title': (
            'This Analyst Sees INTC Stock Hitting $200 In Two Years — '
            'That’s A 106% Upside'
        ),
        'text': (
            'Intel shares could double within two years, driven by '
            'potential manufacturing partnerships with tech giants and '
            'strong demand for AI chips.'
        ),
    },
    {
        'article_id': '6fbdd134-f08f-3f50-a9ca-6ad473caab32',
        'title': (
            'Apple may build AI servers with its own chips and Nvidia '
            'networking'
        ),
        'text': (
            "A reported server project could push Apple's in-house "
            'silicon beyond its own devices and into enterprise '
            'computing.'
        ),
    },
    {
        'article_id': '1dbadf2b-3fe0-3340-b8bd-26e60da3e5a2',
        'title': 'Apple Talks to Nvidia About NVLink for Its Own AI Server',
        'text': (
            'Apple is weighing two configurations, pairing two or four M8'
            ' Ultra chips'
        ),
    },
    {
        'article_id': 'aa2f610a-9207-35d2-a2ba-2e8b2d3d92db',
        'title': (
            "I've Analyzed Hundreds of Stocks in 7 Years. Here's My "
            'Step-by-Step System for Researching Any Company Before '
            'Buying.'
        ),
        'text': (
            "I've been refining my investing process for years, and this "
            'is what I do right now.'
        ),
    },
    {
        'article_id': '456b098e-93e7-3237-9bae-1efc9dd4b43c',
        'title': 'Sector Update: Tech Stocks Mixed Late Afternoon',
        'text': (
            'Tech stocks were mixed late Wednesday afternoon, with the '
            'State Street Technology Select Sector SPDR'
        ),
    },
    {
        'article_id': '3814e01c-4f93-300f-8908-2c8f44c6d33c',
        'title': (
            'The $75,000 Retirement Budget That JEPQ May Struggle to '
            'Support in 10 Years'
        ),
        'text': (
            'A $700,000 JEPQ position clears a $75,000 retirement budget '
            'today, but inflation-adjusted withdrawals over a decade '
            "expose a flaw baked into the fund's design that monthly "
            'distributions alone cannot fix.'
        ),
    },
    {
        'article_id': '4901ca87-fb0e-3bd4-be13-40fbcb31a775',
        'title': 'Should You Buy Qualcomm Stock For The Cash As Apple Leaves?',
        'text': (
            'Qualcomm (QCOM) throws off free cash worth 5.2% of its '
            'market value each year, against 4.4% for the median S&P 500 '
            'company. A yield above the median means one of two things: a'
            ' bargain or a business the market expects to shrink. Here it'
            ' is mostly the second: the cash comes from smartphone chips,'
            ' and Apple is leaving.'
        ),
    },
]


def cache_article(index):
    row = article()
    row.update(CACHE_CASES[index])
    row.update(ticker="AAPL", target_aliases=[], input_mode="committed_cache")
    row["url"] = "https://example.org/recorded/" + str(index)
    return row


class ScriptedLLM:
    def __init__(self, outputs, fenced=False):
        self.outputs = list(outputs)
        self.prompts = []
        self.fenced = fenced
        self.settings = []

    def __call__(self, prompt, **kwargs):
        self.prompts.append(prompt)
        self.settings.append(kwargs)
        value = self.outputs.pop(0)
        raw = value if isinstance(value, str) else json.dumps(value)
        return '```json\n' + raw + '\n```' if self.fenced else raw


class NewsPipelineTests(unittest.TestCase):
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

    def test_strict_parser_rejects_duplicate_keys_and_nonfinite_numbers(self):
        for raw in ('{"x": 1, "x": 2}', '{"x": NaN}'):
            with self.assertRaises(ValueError):
                news.strict_json(raw)

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
            self.assertEqual(calls[0]['max_new_tokens'], 768)
            backend._model.config.max_position_embeddings = 770
            with self.assertRaisesRegex(ValueError, 'context window'):
                news._shared_news_llm('fixture')
            self.assertEqual(len(calls), 1)

    def test_inequalities_and_negative_values_survive_cleaning(self):
        text = 'Net change was -12.5%; EPS < $0.50, not $0.60.'
        self.assertEqual(news.clean_news_text(text), text)

    def test_recorded_award_date_and_metric_fail_together(self):
        row = article()
        row['text_clean'] = (
            'This evening at the 78th Primetime Emmy Awards, Apple TV '
            'shatters records to become the most-awarded network of the '
            'year, landing 29 wins overall.'
        )
        claim = dict.fromkeys(news.STRUCTURED_FIELDS)
        claim.update(
            statement='Apple TV landed 29 wins overall.', evidence_id='E1',
            supporting_text=row['text_clean'], company='Apple',
            metric='most-awarded network', value='29', unit='wins',
            event_date='This evening at the 78th Primetime Emmy Awards',
        )
        with self.assertRaises(ValueError) as caught:
            news.validate_extraction({'claims': [claim]}, row)
        self.assertIn('event_date', str(caught.exception))
        self.assertIn('metric', str(caught.exception))
        corrected = dict(claim, metric='wins', event_date=None)
        news.validate_extraction({'claims': [corrected]}, row)
        self.assertEqual(claim['metric'], 'most-awarded network')
        self.assertEqual(claim['value'], '29')

    def test_event_names_fail_and_partial_calendar_dates_are_kept(self):
        for value in ['This evening at the Awards', '78th Annual Awards',
                      'today', 'Friday']:
            self.assertFalse(news._explicit_event_date(value))
        for value in ['Friday, September 18', 'March 2', '2026-09-18',
                      '18 September 2026', '2026']:
            self.assertTrue(news._explicit_event_date(value))


class RecordedRegressionTests(unittest.TestCase):
    def test_two_apple_stories_and_supplier_relation_have_body_evidence(self):
        for index in [4, 5, 9]:
            row = cache_article(index)
            row['text_clean'] = row['text']
            value = classification(evidence=row['text'])
            value['sentiment'] = 'unknown'
            news.validate_classification(value, row)

    def test_relevance_reason_cannot_contradict_boolean(self):
        row = cache_article(4)
        row['text_clean'] = row['text']
        value = classification(evidence=row['text'])
        value['reason'] = 'This does not directly relate to Apple.'
        with self.assertRaisesRegex(ValueError, 'contradicts'):
            news.validate_classification(value, row)

    def test_target_quote_must_be_real_body_text(self):
        row = cache_article(4)
        row['text_clean'] = row['text']
        for quote in [None, 'Apple confirmed a new factory.']:
            value = classification(evidence=row['text'])
            value['relevance_evidence'] = quote
            with self.assertRaisesRegex(ValueError, 'relevance_evidence'):
                news.validate_classification(value, row)

    def test_supplier_loss_does_not_prove_negative_target_sentiment(self):
        row = cache_article(9)
        row['text_clean'] = row['text']
        value = classification(evidence=row['text'])
        value.update(
            sentiment='negative', sentiment_evidence=row['text'],
            sentiment_reason="Qualcomm may shrink, which is bad for Apple.",
        )
        with self.assertRaisesRegex(ValueError, 'TARGET as subject'):
            news.validate_classification(value, row)
        value.update(sentiment='unknown', sentiment_evidence=None)
        news.validate_classification(value, row)

    def test_promotional_exhibition_is_not_a_target_achievement(self):
        row = article()
        row.update(ticker='AAPL', target_aliases=[], text_clean=(
            'A new photography exhibition, curated by Kathy Ryan, celebrates '
            'the evolving language of visual storytelling and showcases '
            'the advanced pro camera system on iPhone 18 Pro.'
        ))
        value = classification(evidence=row['text_clean'])
        value.update(sentiment='positive',
                     sentiment_evidence=row['text_clean'])
        with self.assertRaisesRegex(ValueError, 'TARGET as subject'):
            news.validate_classification(value, row)
        value.update(sentiment='neutral', sentiment_evidence=None)
        news.validate_classification(value, row)

    def test_explicit_target_achievement_can_be_positive(self):
        row = article()
        row.update(ticker='AAPL', target_aliases=[], text_clean=(
            'Apple TV shatters records, landing 29 wins overall.'
        ))
        value = classification(evidence=row['text_clean'])
        value.update(sentiment='positive',
                     sentiment_evidence=row['text_clean'])
        news.validate_classification(value, row)

    def test_another_subject_and_negation_do_not_prove_direction(self):
        for text in [
            'Apple announced a change, while Qualcomm declined.',
            'Apple has not improved revenue.',
            "Apple's supplier reported a loss.",
        ]:
            row = article()
            row.update(ticker='AAPL', target_aliases=[], text_clean=text)
            value = classification(evidence=text)
            value.update(sentiment='negative' if 'improved' not in text
                         else 'positive', sentiment_evidence=text)
            with self.assertRaisesRegex(ValueError, 'TARGET as subject'):
                news.validate_classification(value, row)

    def test_quantity_qualifier_is_rejected_even_if_in_source(self):
        row = cache_article(8)
        row['text_clean'] = row['text']
        claim = dict.fromkeys(news.STRUCTURED_FIELDS)
        claim.update(statement=row['text'], evidence_id='E1',
                     supporting_text=row['text'], metric='withdrawals',
                     value='inflation-adjusted')
        with self.assertRaisesRegex(ValueError, 'must be a quantity'):
            news.validate_extraction({'claims': [claim]}, row)
        claim.update(value=None, metric=None)
        news.validate_extraction({'claims': [claim]}, row)

    def test_quantities_preserve_source_spelling(self):
        for value in ['$700,000', '-12.5%', '3.75%-4%', '29', 'two or four']:
            self.assertTrue(news._quantity_value(value), value)
        for value in ['inflation-adjusted', 'M8', 'most-awarded', 'growth']:
            self.assertFalse(news._quantity_value(value), value)

    def test_recorded_qualcomm_capitalized_quote_remains_invalid(self):
        row = cache_article(9)
        row['text_clean'] = row['text']
        claim = dict.fromkeys(news.STRUCTURED_FIELDS)
        claim.update(statement='Apple is leaving.', evidence_id='E1',
                     supporting_text='The cash comes from smartphone chips, '
                     'and Apple is leaving.', company='Apple')
        with self.assertRaisesRegex(ValueError, 'exact source span'):
            news.validate_extraction({'claims': [claim]}, row)
        claim['supporting_text'] = (
            'the cash comes from smartphone chips, and Apple is leaving.'
        )
        news.validate_extraction({'claims': [claim]}, row)

    def test_recorded_invented_metric_and_unit_remain_invalid(self):
        row = cache_article(0)
        row['text_clean'] = row['text']
        claim = dict.fromkeys(news.STRUCTURED_FIELDS)
        claim.update(statement=row['text'], evidence_id='E1',
                     supporting_text=row['text'], company='Dell Technologies',
                     metric='stock return', value='334%', unit='percentage')
        with self.assertRaises(ValueError) as error:
            news.validate_extraction({'claims': [claim]}, row)
        self.assertIn('metric', str(error.exception))
        self.assertIn('unit', str(error.exception))

    def test_summary_cannot_add_devices_to_unspecified_configurations(self):
        quote = cache_article(5)['text']
        claim = {'supporting_text': quote}
        value = {'bullets': [{
            'text': 'Apple is considering two configurations for its devices.',
            'claim_ids': ['C1'],
        }], 'limitations': []}
        with self.assertRaisesRegex(ValueError, 'unsupported object'):
            news.validate_summary(value, {'C1': claim})
        value['bullets'][0]['text'] = quote
        news.validate_summary(value, {'C1': claim})


class SentimentEvidenceTests(unittest.TestCase):
    def exhibition_case(self):
        row = article()
        row.update(ticker='AAPL', target_aliases=[], text=(
            'A new photography exhibition, curated by Kathy Ryan, '
            'celebrates the evolving language of visual storytelling '
            'and showcases the advanced pro camera system on iPhone 18 Pro.'
        ))
        row['text_clean'] = row['text']
        value = classification(evidence=row['text'])
        value['sentiment_evidence'] = (
            'The exhibition celebrates the evolving language of visual '
            'storytelling and showcases the advanced pro camera system '
            'on iPhone 18 Pro.'
        )
        return row, value

    def test_recorded_neutral_paraphrase_is_rejected(self):
        row, value = self.exhibition_case()
        with self.assertRaisesRegex(ValueError, 'sentiment_evidence'):
            news.validate_classification(value, row)

    def test_all_labels_reject_nonverbatim_or_invalid_evidence(self):
        row, value = self.exhibition_case()
        for label in news.SENTIMENTS:
            for quote in [value['sentiment_evidence'], '', ' ', 42, [],
                          row['text'].lower()]:
                with self.subTest(label=label, quote=quote):
                    candidate = dict(value, sentiment=label,
                                     sentiment_evidence=quote)
                    with self.assertRaisesRegex(ValueError,
                                                'sentiment_evidence'):
                        news.validate_classification(candidate, row)

    def test_neutral_unknown_accept_exact_quote_or_null(self):
        row, value = self.exhibition_case()
        for label in ('neutral', 'unknown'):
            for quote in (None, row['text'], 'iPhone 18 Pro'):
                news.validate_classification(
                    dict(value, sentiment=label, sentiment_evidence=quote),
                    row,
                )

    def test_directional_labels_still_require_supported_evidence(self):
        row, value = self.exhibition_case()
        for label in ('positive', 'negative', 'mixed'):
            for quote in (None, row['text']):
                with self.assertRaisesRegex(ValueError, 'Directional'):
                    news.validate_classification(
                        dict(value, sentiment=label, sentiment_evidence=quote),
                        row,
                    )


V7_CLASSIFICATION_CASES = [
    (
        (
            'Customers can now shop for Mac mini with M6 and M5 Pro, and '
            'Mac Studio with M5 Max and M5 Ultra, at Apple Store '
            'locations, online, and in the Apple Store app.'
        ),
        (
            'The announcement of new product availability is typically '
            'viewed as a positive development for the company.'
        ),
        (
            'The announcement of new product availability is typically '
            'viewed as a positive development for the company.'
        ),
        None,
    ),
    (
        (
            'On Friday, September 18, Apple Store locations around the '
            'world introduced customers to the iPhone 18 Pro lineup, '
            'Apple Watch Series 12, Apple Watch Ultra 4, and AirPods 5.'
        ),
        (
            'The introduction of new product lineups is typically seen as'
            ' a positive development for the company.'
        ),
        (
            'On Friday, September 18, Apple Store locations around the '
            'world introduced customers to the iPhone 18 Pro lineup, '
            'Apple Watch Series 12, Apple Watch Ultra 4, and AirPods 5.'
        ),
        None,
    ),
    (
        (
            'A new photography exhibition, curated by Kathy Ryan, '
            'celebrates the evolving language of visual storytelling and '
            'showcases the advanced pro camera system on iPhone 18 Pro.'
        ),
        (
            'The exhibition celebrates the evolving language of visual '
            'storytelling and showcases the advanced pro camera system on'
            ' iPhone 18 Pro.'
        ),
        (
            'The exhibition celebrates the evolving language of visual '
            'storytelling and showcases the advanced pro camera system on'
            ' iPhone 18 Pro.'
        ),
        (
            'The exhibition celebrates the evolving language of visual '
            'storytelling and showcases the advanced pro camera system on'
            ' iPhone 18 Pro.'
        ),
    ),
]


class ClassificationRetryFeedbackTests(unittest.TestCase):
    def recorded_case(self, index):
        text, reason, evidence, retry_reason = (
            V7_CLASSIFICATION_CASES[index]
        )
        row = article()
        row.update(ticker='AAPL', target_aliases=[],
                   text=text, text_clean=text)
        wrong = classification(evidence=text)
        wrong.update(category='product', sentiment='positive',
                     sentiment_reason=reason, sentiment_evidence=evidence)
        second = dict(wrong)
        if index < 2:
            second.update(sentiment='neutral', sentiment_reason=retry_reason,
                          sentiment_evidence=None)
        return row, wrong, second

    def remaining_outputs(self, row):
        claim = dict.fromkeys(news.STRUCTURED_FIELDS)
        claim.update(statement=row['text'], evidence_id='E1',
                     supporting_text=row['text'])
        return [
            {'claims': [claim]},
            {'bullets': [{'text': row['text'],
                          'claim_ids': ['fixture-1_C1']}], 'limitations': []},
        ]

    def test_every_label_requires_nonempty_sentiment_reason(self):
        for label in news.SENTIMENTS:
            for reason in (None, '', ' ', 0, [], {}):
                with self.subTest(label=label, reason=reason):
                    value = dict(classification(), sentiment=label,
                                 sentiment_reason=reason)
                    with self.assertRaisesRegex(ValueError,
                                                'sentiment_reason'):
                        news.validate_classification(value)

    def test_feedback_handles_malformed_responses_without_mutating_them(self):
        row, _, _ = self.recorded_case(0)
        for parsed in (None, [], 'not JSON', {},
                       {'sentiment': [], 'sentiment_reason': {},
                        'sentiment_evidence': 42}):
            original = deepcopy(parsed)
            feedback = news._classification_retry_feedback(parsed, row)
            self.assertIn('CLASSIFICATION FIELD FEEDBACK', feedback)
            self.assertEqual(parsed, original)


class SentenceContextRegressionTests(unittest.TestCase):
    def award_case(self):
        row = article()
        row.update(ticker='AAPL', target_aliases=[], text=(
            'This evening at the 78th Primetime Emmy Awards, Apple TV '
            'shatters records to become the most-awarded network of the '
            'year, landing 29 wins overall.'
        ))
        wrong = dict.fromkeys(news.STRUCTURED_FIELDS)
        wrong.update(
            statement='Apple TV becomes the most-awarded network of the year',
            evidence_id='E1', supporting_text=row['text'], company='Apple',
            metric='most-awarded network', value='29', unit='wins',
        )
        return row, {'claims': [wrong]}

    def award_classification(self):
        row, extraction = self.award_case()
        row['text_clean'] = row['text']
        quote = ('shatters records to become the most-awarded network of '
                 'the year, landing 29 wins overall.')
        value = classification(evidence=row['text'])
        value.update(
            category='other', sentiment='positive',
            sentiment_reason='The source reports an award achievement.',
            sentiment_evidence=quote,
        )
        extraction['claims'][0].update(metric='wins')
        return row, value, extraction

    def test_other_subject_or_sentence_cannot_supply_target_direction(self):
        quote = 'won three industry awards.'
        for text in [
            'Apple opened a store. Qualcomm won three industry awards.',
            'Apple opened a store, while Qualcomm won three industry awards.',
            'Apple said Qualcomm won three industry awards.',
            "Apple's supplier won three industry awards.",
            'Apple has not won three industry awards.',
        ]:
            row = article()
            row.update(ticker='AAPL', target_aliases=[], text_clean=text)
            value = classification(evidence=text)
            value.update(sentiment='positive', sentiment_evidence=quote)
            with self.subTest(text=text):
                with self.assertRaisesRegex(ValueError, 'Directional'):
                    news.validate_classification(value, row)

    def test_direction_word_outside_quote_cannot_support_product_praise(self):
        text = 'Apple won awards for a new camera.'
        row = article()
        row.update(ticker='AAPL', target_aliases=[], text_clean=text)
        value = classification(evidence=text)
        value.update(sentiment='positive', sentiment_evidence='a new camera')
        with self.assertRaisesRegex(ValueError, 'Directional'):
            news.validate_classification(value, row)

    def test_repeated_short_quote_needs_unambiguous_context(self):
        text = ('Apple won three industry awards. '
                'Qualcomm won three industry awards.')
        row = article()
        row.update(ticker='AAPL', target_aliases=[], text_clean=text)
        value = classification(evidence='Apple won three industry awards.')
        value.update(sentiment='positive',
                     sentiment_evidence='won three industry awards.')
        with self.assertRaisesRegex(ValueError, 'Directional'):
            news.validate_classification(value, row)
        value['sentiment_evidence'] = 'Apple won three industry awards.'
        news.validate_classification(value, row)

    def test_context_expansion_keeps_paraphrases_invalid(self):
        row, value, _ = self.award_classification()
        value['sentiment_evidence'] = 'Shatters records to become the best.'
        with self.assertRaisesRegex(ValueError, 'sentiment_evidence'):
            news.validate_classification(value, row)

    def test_synthetic_example_cannot_be_used_as_article_evidence(self):
        row, value, _ = self.award_classification()
        value['sentiment_evidence'] = 'Cedar Labs won three industry awards.'
        with self.assertRaisesRegex(ValueError, 'sentiment_evidence'):
            news.validate_classification(value, row)


class EventFirstPolicyTests(unittest.TestCase):
    def record(self, text, event, label='positive', category='product'):
        row = article()
        row.update(ticker='AAPL', target_aliases=[],
                   text=text, text_clean=text)
        value = classification(evidence=text)
        value.update(event_type=event, category=category, sentiment=label,
                     sentiment_evidence=text,
                     sentiment_reason='The source describes this event.')
        return row, value

    def test_award_source_cannot_claim_financial_event_or_earnings(self):
        row, value = self.record('Apple TV won three awards.', 'financial',
                                 category='earnings')
        with self.assertRaisesRegex(ValueError, 'financial'):
            news._event_policy_output(value, row)
        value.update(event_type='other')
        with self.assertRaisesRegex(ValueError, 'earnings'):
            news.validate_classification(value, row)

    def test_financial_growth_plus_launch_is_not_neutralized(self):
        text = 'Apple revenue rose 10%. Apple introduced a new phone.'
        row, value = self.record(text, 'availability')
        with self.assertRaisesRegex(ValueError, 'material'):
            news._event_policy_output(value, row)
        value.update(event_type='financial', category='earnings')
        output, _ = news._event_policy_output(value, row)
        news.validate_classification(output, row)
        self.assertEqual(output['sentiment'], 'positive')

    def test_awards_do_not_erase_financial_losses_or_recalls(self):
        for text in [
            'Apple won three awards. Apple revenue declined 20%.',
            'Apple won three awards. Apple announced a recall.',
        ]:
            row, value = self.record(text, 'award', label='mixed')
            with self.assertRaisesRegex(ValueError, 'only material event'):
                news._event_policy_output(value, row)
            value.update(event_type='other', category='other')
            output, changes = news._event_policy_output(value, row)
            news.validate_classification(output, row)
            self.assertEqual(output['sentiment'], 'mixed')
            self.assertEqual(changes, [])

    def test_venue_keyword_and_forecast_cannot_fabricate_award(self):
        for text, event in [
            ('Apple opened an investigation.', 'opening'),
            ('Apple may win three awards.', 'award'),
            ('Apple was nominated for three awards.', 'award'),
            (V7_CLASSIFICATION_CASES[2][0], 'award'),
        ]:
            row, value = self.record(text, event)
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    news._event_policy_output(value, row)

    def test_supplier_loss_does_not_derive_negative_target_sentiment(self):
        text = 'Qualcomm revenue declined because Apple is leaving.'
        row, value = self.record(text, 'financial', label='negative',
                                 category='earnings')
        output, _ = news._event_policy_output(value, row)
        with self.assertRaisesRegex(ValueError, 'Directional'):
            news.validate_classification(output, row)

    def test_rule_derivation_does_not_hide_paraphrased_evidence(self):
        row, value = self.record(V7_CLASSIFICATION_CASES[2][0], 'showcase')
        value['sentiment_evidence'] = 'Apple has a great photography exhibit.'
        with self.assertRaisesRegex(ValueError, 'sentiment_evidence'):
            news._event_policy_output(value, row)

    def test_event_policy_generalizes_to_another_target(self):
        row = article()
        row.update(ticker='TEST', target_aliases=['Cedar Labs'],
                   text_clean='Cedar Labs introduced a new phone.')
        value = classification(evidence=row['text_clean'])
        value.update(event_type='availability', category='product',
                     sentiment='positive')
        output, _ = news._event_policy_output(value, row)
        news.validate_classification(output, row)
        self.assertEqual(output['sentiment'], 'neutral')


class ScopeAndPlansTests(unittest.TestCase):
    def test_planned_projects_accept_unknown_other_product(self):
        for index in [4, 5]:
            row = cache_article(index)
            row['text_clean'] = row['text']
            value = classification(evidence=row['text'])
            value.update(category='product', sentiment='unknown',
                         sentiment_reason='Project impact is not stated.')
            news.validate_classification(value, row)
            value['event_type'] = 'showcase'
            with self.assertRaisesRegex(ValueError, 'source event evidence'):
                news.validate_classification(value, row)

    def test_supplier_negative_is_not_target_negative(self):
        row = cache_article(9)
        row['text_clean'] = row['text']
        value = classification(evidence=row['text'])
        value.update(event_type='supply_chain', category='supply_chain',
                     sentiment='unknown',
                     sentiment_reason='Apple impact is not stated.')
        news.validate_classification(value, row)
        value.update(sentiment='negative', sentiment_evidence=(
            'Here it is mostly the second: the cash comes from smartphone '
            'chips, and Apple is leaving.'
        ))
        with self.assertRaisesRegex(ValueError, 'TARGET'):
            news.validate_classification(value, row)

    def test_prompt_has_no_exhibition_example_to_copy(self):
        row = cache_article(4)
        row, = news.prepare_news([row])[0]
        prompt = news._classification_prompt(row)
        self.assertNotIn('Cedar Labs', prompt)
        self.assertNotIn('SYNTHETIC DECISION EXAMPLES', prompt)
        self.assertIn('PLANNED EVENTS', prompt)
        self.assertIn('Decide target relevance first', prompt)

    def test_title_cannot_replace_body_evidence(self):
        row = cache_article(5)
        row['text_clean'] = row['text']
        value = classification(evidence=row['title'])
        with self.assertRaisesRegex(ValueError, 'ground the target event'):
            news.validate_classification(value, row)


class EvidenceSelectionTests(unittest.TestCase):
    def test_legacy_bad_quote_is_audited_not_used_as_evidence(self):
        row = cache_article(9)
        row['text_clean'] = row['text']
        claim = dict.fromkeys(news.STRUCTURED_FIELDS)
        claim.update(statement='Apple is leaving.', evidence_id='E1',
                     supporting_text='The cash comes from smartphone chips, '
                                     'and Apple is leaving.')
        raw = {'claims': [claim]}
        original = deepcopy(raw)
        for _ in range(2):
            output, changes = news._extraction_evidence_output(raw, row)
            news.validate_extraction(output, row)
            self.assertEqual(output['claims'][0]['supporting_text'],
                             row['text'])
            self.assertEqual(raw, original)
            self.assertTrue(changes)

    def test_source_copy_does_not_approve_invented_unit(self):
        row = cache_article(9)
        row['text_clean'] = row['text']
        claim = dict.fromkeys(news.STRUCTURED_FIELDS)
        claim.update(statement='Qualcomm has free cash worth 5.2%.',
                     evidence_id='E1', company='Qualcomm', metric='free cash',
                     value='5.2', unit='percentage')
        output, _ = news._extraction_evidence_output({'claims': [claim]}, row)
        with self.assertRaisesRegex(ValueError, 'unit'):
            news.validate_extraction(output, row)
        output['claims'][0]['unit'] = '%'
        news.validate_extraction(output, row)

    def configuration_replies(self):
        row = cache_article(5)
        value = classification(evidence=row['text'])
        value.update(category='product', sentiment='unknown')
        claim = dict.fromkeys(news.STRUCTURED_FIELDS)
        claim.update(statement=row['text'], evidence_id='E1', company='Apple')
        bad = {'bullets': [{
            'text': 'Apple is considering two device configurations, '
                    'using two or four M8 Ultra chips.',
            'claim_ids': [row['article_id'] + '_C1'],
        }], 'limitations': []}
        return row, value, {'claims': [claim]}, bad


class ExtractionFieldRegressionTests(unittest.TestCase):
    def unit_case(self):
        row = cache_article(9)
        row['text_clean'] = row['text']
        claim = dict.fromkeys(news.STRUCTURED_FIELDS)
        claim.update(statement='Qualcomm throws off free cash worth 5.2% '
                     'of its market value each year.', evidence_id='E1',
                     company='Qualcomm', metric='free cash', value='5.2',
                     unit='percentage')
        return row, {'claims': [claim]}

    def configuration_case(self):
        row = cache_article(5)
        label = classification(evidence=row['text'])
        label.update(category='product', sentiment='unknown')
        claim = dict.fromkeys(news.STRUCTURED_FIELDS)
        claim.update(statement='Apple is considering two configurations '
                     'for its devices, pairing two or four M8 Ultra chips.',
                     evidence_id='E1', company='Apple')
        return row, label, {'claims': [claim]}

    def test_object_guard_uses_evidence_not_title(self):
        row, label, value = self.configuration_case()
        row['text_clean'] = row['text']
        for noun in ['device', 'Devices', 'server', 'SERVERS']:
            candidate = deepcopy(value)
            candidate['claims'][0]['statement'] = 'Apple considers ' + noun
            output, _ = news._extraction_evidence_output(candidate, row)
            with self.assertRaisesRegex(ValueError, 'unsupported object'):
                news.validate_extraction(output, row)
        row = cache_article(4)
        row['text_clean'] = row['text']
        candidate = deepcopy(value)
        candidate['claims'][0]['statement'] = row['text']
        output, _ = news._extraction_evidence_output(candidate, row)
        news.validate_extraction(output, row)


class SentenceExtractionTests(unittest.TestCase):
    def row(self, index=5):
        row = cache_article(index)
        return news.prepare_news([row])[0][0]

    def empty_numbers(self):
        return {'measurements': [], 'event_date': None, 'period': None}

    def numeric_case(self):
        row = self.row(9)
        sentence = news.evidence_sentences(row)[0]
        spans = news.numeric_spans(sentence)
        value = self.empty_numbers()
        value['measurements'] = [
            {'span_id': 'E1.N1', 'company': 'Qualcomm',
             'metric': 'free cash', 'value': '5.2', 'unit': '%'},
            {'span_id': 'E1.N2', 'company': 'median S&P 500 company',
             'metric': 'free cash', 'value': '4.4', 'unit': '%'},
        ]
        return sentence, spans, value

    def test_sentence_offsets_preserve_decimals_and_source(self):
        row = self.row(9)
        sentences = news.evidence_sentences(row)
        self.assertEqual(len(sentences), 3)
        self.assertIn('5.2%', sentences[0]['text'])
        self.assertIn('4.4%', sentences[0]['text'])
        for sentence in sentences:
            original = row['text_clean'][sentence['start']:sentence['end']]
            self.assertEqual(original, sentence['text'])

    def test_event_selection_requires_target_and_unique_known_ids(self):
        row = self.row(9)
        sentences = news.evidence_sentences(row)
        news.validate_event_selection({'event_ids': ['E3', 'E1']},
                                      sentences, row)
        for ids in [[], ['E1'], ['E99'], ['E3', 'E3'], ['E3'] * 7]:
            with self.assertRaises(ValueError):
                news.validate_event_selection({'event_ids': ids},
                                              sentences, row)

    def test_numeric_owners_remain_on_their_side_of_comparison(self):
        sentence, spans, value = self.numeric_case()
        news.validate_numeric_output(value, sentence, spans)
        for field, bad in [('company', 'Qualcomm'), ('value', '5.2')]:
            wrong = deepcopy(value)
            wrong['measurements'][1][field] = bad
            with self.assertRaises(ValueError):
                news.validate_numeric_output(wrong, sentence, spans)

    def test_repeated_excessive_or_wrong_unit_numbers_fail(self):
        sentence, spans, value = self.numeric_case()
        for wrong in [
            dict(value, measurements=value['measurements'] * 2),
            dict(value, measurements=[value['measurements'][0]] * 2),
        ]:
            with self.assertRaises(ValueError):
                news.validate_numeric_output(wrong, sentence, spans)
        value['measurements'][0]['unit'] = 'percentage'
        with self.assertRaises(ValueError):
            news.validate_numeric_output(value, sentence, spans)

    def test_value_unit_pair_and_model_name_are_checked(self):
        sentence, spans, value = self.numeric_case()
        value['measurements'][0]['value'] = '15.2'
        with self.assertRaises(ValueError):
            news.validate_numeric_output(value, sentence, spans)
        value['measurements'][0]['value'] = 'Qualcomm'
        with self.assertRaises(ValueError):
            news.validate_numeric_output(value, sentence, spans)

    def test_event_date_is_not_publication_metadata(self):
        sentence, spans, value = self.numeric_case()
        value['event_date'] = '2026-09-16'
        with self.assertRaises(ValueError):
            news.validate_numeric_output(value, sentence, spans)

    def test_configuration_statement_is_copied_not_generated(self):
        row = self.row()
        label = classification(evidence=row['text_clean'])
        label.update(category='product', sentiment='unknown')
        summary = {'bullets': [{'text': row['text_clean'],
                               'claim_ids': [row['article_id'] + '_C1']}],
                   'limitations': []}
        model = ScriptedLLM([label, {'event_ids': ['E1']},
                            self.empty_numbers(), summary])
        result = report.run_news_chain([row], llm=model)
        self.assertEqual(result['status'], 'needs_manual_review')
        claim = result['claims'][0]
        self.assertEqual(claim['statement'], row['text_clean'])
        self.assertNotIn('devices', claim['statement'])
        self.assertEqual(claim['statement_origin'],
                         'application_copied_selected_sentence')
        self.assertEqual([t['stage'] for t in result['trace']],
                         ['classify', 'select_events', 'extract_numbers',
                          'summarize'])
        self.assertTrue(all(s['temperature'] == 0 for s in model.settings))

    def test_selection_prose_and_unclosed_output_stay_failed(self):
        row = self.row()
        label = classification(evidence=row['text_clean'])
        for bad in ['{"event_ids":["E1"]',
                    {'event_ids': ['E1'], 'statement': 'Apple devices'}]:
            result = news.run_news_chain([row], llm=ScriptedLLM(
                [label, bad, bad]
            ))
            self.assertEqual(result['status'], 'needs_review')
            self.assertEqual(result['claims'], [])
            self.assertEqual(result['article_results'][0]['status'],
                             'event_selection_failed')
            self.assertEqual(len(result['trace']), 3)

    def test_numeric_failure_preserves_event_but_not_failed_numbers(self):
        row = self.row()
        label = classification(evidence=row['text_clean'])
        bad = '{"measurements":['
        summary = {'bullets': [{'text': row['text_clean'],
                               'claim_ids': [row['article_id'] + '_C1']}],
                   'limitations': []}
        result = news.run_news_chain([row], llm=ScriptedLLM(
            [label, {'event_ids': ['E1']}, bad, bad, summary]
        ))
        self.assertEqual(result['status'], 'needs_review')
        self.assertEqual(result['claims'][0]['statement'], row['text_clean'])
        self.assertEqual(result['claims'][0]['numeric_status'], 'failed')
        self.assertEqual(result['claims'][0]['measurements'], [])
        self.assertEqual(result['validation_summary']['unresolved_errors'], 2)
        self.assertEqual(result['trace'][2]['raw_response'], bad)
        self.assertTrue(any('partial result' in x for x in
                            result['stages']['summarize']['limitations']))

    def test_supplier_event_and_comparison_are_preserved_separately(self):
        row = self.row(9)
        sentence, spans, numbers = self.numeric_case()
        label = classification(evidence=row['text_clean'])
        label.update(category='supply_chain', sentiment='unknown')
        sentences = news.evidence_sentences(row)
        summary = {'bullets': [
            {'text': sentences[2]['text'],
             'claim_ids': [row['article_id'] + '_C1']},
            {'text': sentences[0]['text'],
             'claim_ids': [row['article_id'] + '_C2']},
        ], 'limitations': []}
        result = news.run_news_chain([row], llm=ScriptedLLM([
            label, {'event_ids': ['E3', 'E1']}, self.empty_numbers(),
            numbers, summary,
        ]))
        self.assertEqual(result['status'], 'needs_manual_review')
        self.assertIn('Apple is leaving', result['claims'][0]['statement'])
        claim = result['claims'][1]
        self.assertIsNone(claim['company'])
        self.assertIsNone(claim['value'])
        self.assertEqual(claim['measurements'][0]['company'], 'Qualcomm')
        self.assertEqual(claim['measurements'][1]['company'],
                         'median S&P 500 company')
        self.assertEqual(claim['measurements'][1]['owner_role'], 'comparison')

    def test_empty_and_scope_excluded_inputs_do_not_call_model(self):
        for rows in [[], [cache_article(i) for i in [0, 1, 2, 3, 6, 7, 8]]]:
            model = ScriptedLLM([])
            result = news.run_news_chain(rows, llm=model)
            self.assertEqual(model.prompts, [])
            self.assertEqual(result['trace'], [])

    def test_retry_corrects_number_owner_without_overwriting_raw(self):
        row = self.row(9)
        sentence, spans, good = self.numeric_case()
        wrong = deepcopy(good)
        wrong['measurements'][1]['company'] = 'Qualcomm'
        label = classification(evidence=row['text_clean'])
        label['sentiment'] = 'unknown'
        sentences = news.evidence_sentences(row)
        summary = {'bullets': [
            {'text': sentences[2]['text'],
             'claim_ids': [row['article_id'] + '_C1']},
            {'text': sentences[0]['text'],
             'claim_ids': [row['article_id'] + '_C2']},
        ], 'limitations': []}
        result = news.run_news_chain([row], llm=ScriptedLLM([
            label, {'event_ids': ['E3', 'E1']}, self.empty_numbers(),
            wrong, good, summary,
        ]))
        self.assertEqual(result['status'], 'needs_manual_review')
        self.assertEqual(result['trace'][3]['parsed'], wrong)
        self.assertTrue(result['trace'][3]['resolved_by_retry'])

    def test_no_quantity_retries_can_recover_or_remain_failed(self):
        for index, eid, phrase, owner, metric in [
            (4, 'E1', 'beyond its own devices', 'Apple', 'in-house silicon'),
            (9, 'E3', 'mostly the second', 'Apple', 'cash'),
        ]:
            row = self.row(index)
            sentence = next(s for s in news.evidence_sentences(row)
                            if s['evidence_id'] == eid)
            bad = self.empty_numbers()
            bad['measurements'] = [{
                'span_id': eid + '.N1', 'company': owner,
                'metric': metric, 'value': phrase, 'unit': None,
            }]
            label = classification(evidence=row['text_clean'])
            label['sentiment'] = 'unknown'
            summary = {'bullets': [{
                'text': sentence['text'],
                'claim_ids': [row['article_id'] + '_C1'],
            }], 'limitations': []}
            for corrected in [False, True]:
                retry = self.empty_numbers() if corrected else bad
                model = ScriptedLLM([
                    label, {'event_ids': [eid]}, bad, retry, summary,
                ])
                result = news.run_news_chain([row], llm=model)
                self.assertEqual(result['trace'][2]['parsed'], bad)
                self.assertIn('measurements[0].value',
                              result['trace'][2]['error'])
                self.assertIn('measurements: []', model.prompts[3])
                self.assertEqual(result['claims'][0]['numeric_status'],
                                 'needs_manual_review' if corrected
                                 else 'failed')
                self.assertEqual(result['status'], 'needs_manual_review'
                                 if corrected else 'needs_review')

    def test_comparator_cannot_drop_median_company(self):
        sentence, spans, valid = self.numeric_case()
        for owner in ['S&P 500', 'S&P 500 company', None]:
            bad = deepcopy(valid)
            bad['measurements'][1]['company'] = owner
            with self.assertRaisesRegex(ValueError, 'full comparison subject'):
                news.validate_numeric_output(bad, sentence, spans)
        news.validate_numeric_output(valid, sentence, spans)

    def test_departure_summary_is_not_zero_contribution_or_completed(self):
        support = 'The cash comes from chips, and Apple is leaving.'
        claims = {'c1': {'supporting_text': support}}
        for text in ['Apple is not contributing.', 'Apple has left.',
                     'Apple is leaving and is not contributing.']:
            summary = {'bullets': [{'text': text, 'claim_ids': ['c1']}],
                       'limitations': []}
            with self.assertRaisesRegex(ValueError, 'ongoing departure'):
                news.validate_summary(summary, claims)
        summary['bullets'][0]['text'] = 'Apple is leaving.'
        news.validate_summary(summary, claims)

    def test_departure_retry_preserves_failed_raw_outputs(self):
        row = self.row(9)
        label = classification(evidence=row['text_clean'])
        label['sentiment'] = 'unknown'
        bad = {'bullets': [{'text': 'Apple is not contributing.',
                           'claim_ids': [row['article_id'] + '_C1']}],
               'limitations': []}
        good = deepcopy(bad)
        good['bullets'][0]['text'] = 'Apple is leaving.'
        for corrected in [False, True]:
            result = news.run_news_chain([row], llm=ScriptedLLM([
                label, {'event_ids': ['E3']}, self.empty_numbers(),
                bad, good if corrected else bad,
            ]))
            self.assertEqual(result['trace'][3]['parsed'], bad)
            self.assertEqual(result['trace'][3]['resolved_by_retry'],
                             corrected)
            self.assertEqual(result['status'], 'needs_manual_review'
                             if corrected else 'needs_review')


if __name__ == '__main__':
    unittest.main(verbosity=2)
