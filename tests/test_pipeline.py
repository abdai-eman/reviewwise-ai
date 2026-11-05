"""Offline logic tests. Mock responses here are NOT evidence of working AI."""

import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import httpx
from pydantic import ValidationError

from reviewwise.config import MAX_REVIEWS, MODEL
from reviewwise.pipeline import (
    Analysis, BatchResult, Extraction, Review, ReviewWiseError, analyze_reviews,
    complaint_rows, extract_review, make_reviews, require_model,
    reviews_from_csv, reviews_from_text, validate_extraction,
)
from reviewwise.report import render_report, reporting_week, suggested_actions
from reviewwise.evidence import evidence_units, response_schema, decode_packet


ROOT = Path(__file__).resolve().parent.parent


def response(content):
    return SimpleNamespace(message=SimpleNamespace(content=content))


def stream_response(content):
    yield response(content)


def packet(number, unit=0, category="cold_coffee"):
    return json.dumps({"results": [{"id": number, "positive": [], "complaints": [{"unit": unit, "category": category}]}]})


class InputTests(unittest.TestCase):
    def test_multilingual_input_keeps_original_text_and_assigns_ids(self):
        reviews = reviews_from_text("  Café froid.\n\nDe Kaffi war kal.  ")
        self.assertEqual(reviews, [Review(1, "Café froid."), Review(2, "De Kaffi war kal.")])

    def test_empty_oversized_and_too_many_reviews_are_rejected(self):
        for texts in ([], [" "], ["x" * 2001], ["review"] * (MAX_REVIEWS + 1)):
            with self.subTest(texts=len(texts)), self.assertRaises(ReviewWiseError):
                make_reviews(texts)

    def test_csv_supports_bom_multiline_quotes_and_accents(self):
        data = '\ufeffreview,unused\r\n"Café froid.\nPersonnel gentil.",ignore\r\n'.encode("utf-8")
        self.assertEqual(reviews_from_csv(data), [Review(1, "Café froid.\nPersonnel gentil.")])

    def test_bad_csv_is_explained(self):
        for data in (b"text\ncoffee", b"review,review\na,b", b"review\na,b", b'\xff', b'review\n"unterminated'):
            with self.subTest(data=data), self.assertRaises(ReviewWiseError):
                reviews_from_csv(data)

    def test_weekly_csv_accepts_all_eighty_reviews(self):
        data = ("review\n" + "\n".join(f"Review {i}: Cold coffee." for i in range(1, 81))).encode("utf-8")
        reviews = reviews_from_csv(data)
        self.assertEqual(len(reviews), 80)
        self.assertEqual(reviews[-1], Review(80, "Review 80: Cold coffee."))

    def test_documented_weekly_limit_is_accepted(self):
        self.assertEqual(len(make_reviews(["Cold coffee."] * MAX_REVIEWS)), MAX_REVIEWS)


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.review = Review(7, "Le café était froid, mais le personnel était sympathique.")
        self.good = json.dumps({
            "positives": ["le personnel était sympathique"],
            "complaints": [{"category": "cold_coffee", "quote": "Le café était froid"}],
        })

    def test_exact_nonenglish_evidence_is_accepted(self):
        extraction = validate_extraction(self.good, self.review)
        self.assertEqual(extraction.complaints[0].category, "cold_coffee")

    def test_invented_or_empty_evidence_is_rejected(self):
        for quote in ("the coffee was cold", "", " "):
            data = json.dumps({"positives": [quote], "complaints": []})
            with self.subTest(quote=quote), self.assertRaises(ValueError):
                validate_extraction(data, self.review)

    def test_unknown_categories_extra_keys_and_bad_types_are_rejected(self):
        invalid = [
            {"positives": [], "complaints": [{"category": "service", "quote": "Le café"}]},
            {"positives": [], "complaints": [], "count": 10},
            {"positives": "friendly", "complaints": []},
        ]
        for data in invalid:
            with self.subTest(data=data), self.assertRaises(ValidationError):
                validate_extraction(json.dumps(data), self.review)

    def test_retry_is_bounded_and_uses_structured_output(self):
        client = Mock()
        client.chat.side_effect = [stream_response("not JSON"), stream_response(packet(7))]
        self.assertEqual(extract_review(client, self.review).complaints[0].category, "cold_coffee")
        self.assertEqual(client.chat.call_count, 2)
        self.assertEqual(client.chat.call_args.kwargs["model"], MODEL)
        self.assertEqual(client.chat.call_args.kwargs["format"], response_schema([self.review]))
        self.assertEqual(client.chat.call_args.kwargs["options"]["temperature"], 0)
        self.assertLessEqual(client.chat.call_args.kwargs["options"]["num_threads"], 2)
        self.assertEqual(client.chat.call_args.kwargs["options"]["num_ctx"], 2048)
        self.assertTrue(client.chat.call_args.kwargs["stream"])

    def test_invalid_extraction_and_timeout_do_not_fabricate_success(self):
        client = Mock()
        client.chat.side_effect = lambda **kwargs: stream_response("{}")
        with self.assertRaisesRegex(ReviewWiseError, "failed validation"):
            extract_review(client, self.review)
        self.assertEqual(client.chat.call_count, 2)
        client.chat.side_effect = httpx.ReadTimeout("test timeout")
        with self.assertRaisesRegex(ReviewWiseError, "timed out"):
            extract_review(client, self.review)

    def test_unavailable_ollama_and_missing_model_have_specific_messages(self):
        client = Mock()
        client.list.side_effect = ConnectionError("test connection failure")
        with self.assertRaisesRegex(ReviewWiseError, "Ollama is unavailable"):
            require_model(client)
        client.list.side_effect = None
        client.list.return_value = SimpleNamespace(models=[])
        with self.assertRaisesRegex(ReviewWiseError, "model is missing"):
            require_model(client)

    def test_service_failure_retains_validated_results_and_lists_pending_reviews(self):
        with patch("reviewwise.pipeline.local_client") as factory:
            client = factory.return_value.__enter__.return_value
            client.list.return_value = SimpleNamespace(models=[SimpleNamespace(model=MODEL, digest="test")])
            client.chat.side_effect = [stream_response(packet(1)), ConnectionError("test disconnect")]
            result = analyze_reviews(make_reviews([self.review.text, "The service was slow. " + "x" * 1500]))
            self.assertEqual(len(result.analyses), 1)
            self.assertEqual([review.number for review in result.pending], [2])
            self.assertFalse(result.complete)
            self.assertEqual(result.total_reviews, 2)
            self.assertIn("Ollama", result.stop_reason)


class SessionReuseTests(unittest.TestCase):
    """Offline fixtures verify reuse mechanics, never real-model speed or accuracy."""

    def setUp(self):
        patcher = patch("reviewwise.pipeline.local_client")
        self.addCleanup(patcher.stop)
        self.client = patcher.start().return_value.__enter__.return_value
        self.client.list.return_value = SimpleNamespace(models=[SimpleNamespace(model=MODEL, digest="fixture-A")])

        def answer(**kwargs):
            reviews = json.loads(kwargs["messages"][1]["content"])["reviews"]
            return stream_response(json.dumps({"results": [
                {"id": item["id"], "positive": [], "complaints": [{"category": "cold_coffee", "unit": 0}]}
                for item in reviews
            ]}))

        self.answer = answer
        self.client.chat.side_effect = answer

    def test_all_eighty_reviews_are_counted_and_repeated_report_avoids_new_ai_calls(self):
        reviews = make_reviews([f"Cold coffee, review {i}." for i in range(1, 81)])
        cache = {}
        first = analyze_reviews(reviews, cache=cache)
        self.assertEqual(self.client.chat.call_count, 20)
        self.assertEqual(len(first.analyses), 80)
        self.assertEqual(first.reused_reviews, 0)
        self.client.chat.reset_mock()
        progress = Mock()
        second = analyze_reviews(reviews, cache=cache, progress=progress)
        self.client.chat.assert_not_called()
        self.assertEqual(second.reused_reviews, 80)
        self.assertEqual(complaint_rows(second.analyses)[0]["Reviews"], 80)
        self.assertEqual(complaint_rows(second.analyses)[0]["Review numbers"], ", ".join(map(str, range(1, 81))))
        self.assertEqual(progress.call_count, 80)
        progress.assert_called_with(80, 80)
        report = render_report(second, reporting_day=date(2026, 11, 4))
        self.assertIn("Reviews analyzed: 80", report)
        self.assertIn("Review 80: Cold coffee, review 80.", report)
        self.assertIn("New AI analyses: 0", report)
        self.assertIn("reused from this session: 80", report)

    def test_failed_report_can_resume_from_completed_validated_reviews(self):
        reviews = make_reviews([f"Cold coffee {i}." for i in range(1, 9)])
        cache = {}
        self.client.chat.side_effect = [
            self.answer(messages=[None, {"content": json.dumps({"reviews": [{"id": i} for i in range(1, 5)]})}]),
            ConnectionError("fixture disconnect"),
        ]
        partial = analyze_reviews(reviews, cache=cache)
        self.assertEqual(len(partial.analyses), 4)
        self.assertEqual(len(partial.pending), 4)
        self.assertFalse(partial.complete)
        self.assertEqual(len(cache), 4)
        self.client.chat.reset_mock()
        self.client.chat.side_effect = self.answer
        result = analyze_reviews(reviews, cache=cache)
        self.assertEqual(self.client.chat.call_count, 1)
        self.assertEqual(result.reused_reviews, 4)
        self.assertEqual(len(result.analyses), 8)

    def test_identical_text_reuses_extraction_but_each_input_row_still_counts(self):
        result = analyze_reviews(make_reviews(["Cold coffee."] * 80), cache={})
        self.client.chat.assert_called_once()
        self.assertEqual(result.reused_reviews, 79)
        self.assertEqual(complaint_rows(result.analyses)[0]["Reviews"], 80)

    def test_model_prompt_and_generation_changes_require_fresh_extraction(self):
        reviews, cache = make_reviews(["Cold coffee."]), {}
        analyze_reviews(reviews, cache=cache)
        self.client.list.return_value.models[0].digest = "fixture-B"
        analyze_reviews(reviews, cache=cache)
        with patch("reviewwise.pipeline.COMPACT_PROMPT", "Different fixture prompt"):
            analyze_reviews(reviews, cache=cache)
        with patch("reviewwise.pipeline.EXTRACTION_OPTIONS", {"temperature": 0, "num_ctx": 2048, "num_predict": 1024}):
            analyze_reviews(reviews, cache=cache)
        self.assertEqual(self.client.chat.call_count, 4)

    def test_invalid_cached_evidence_is_rejected_and_extracted_again(self):
        reviews, cache = make_reviews(["Cold coffee."]), {}
        analyze_reviews(reviews, cache=cache)
        cache[next(iter(cache))] = json.dumps({"positives": ["Invented praise"], "complaints": []})
        result = analyze_reviews(reviews, cache=cache)
        self.assertEqual(self.client.chat.call_count, 2)
        self.assertEqual(result.reused_reviews, 0)
        self.assertEqual(complaint_rows(result.analyses)[0]["Reviews"], 1)

    def test_invalid_review_twelve_does_not_discard_or_stop_other_reviews(self):
        original_answer = self.answer

        def answer(**kwargs):
            items = json.loads(kwargs["messages"][1]["content"])["reviews"]
            return stream_response('{}') if any(item['id'] == 12 for item in items) else original_answer(**kwargs)

        self.client.chat.side_effect = answer
        updates = []
        result = analyze_reviews(make_reviews([f"Cold coffee {i}." for i in range(1, 81)]), cache={}, on_update=updates.append)
        self.assertEqual(len(result.analyses), 79)
        self.assertEqual([item.review.number for item in result.failures], [12])
        self.assertEqual(len(result.pending), 0)
        self.assertFalse(result.complete)
        self.assertEqual(result.total_reviews, 80)
        self.assertTrue(any(0 < len(item.analyses) < 79 and item.running for item in updates))
        report = render_report(result)
        self.assertIn('PARTIAL', report)
        self.assertIn('Reviews analyzed: 79', report)
        self.assertIn('Review 80:', report)
        self.assertIn('Review 12: Cold coffee 12.', report)
        self.assertIn('REVIEWS NEEDING ATTENTION', report)

    def test_cancelling_closes_stream_and_preserves_pending_reviews(self):
        stopped = False
        closed = []

        def stream(**kwargs):
            nonlocal stopped
            try:
                stopped = True
                yield response('{')
            finally:
                closed.append(True)

        self.client.chat.side_effect = stream
        result = analyze_reviews(make_reviews(['Cold coffee.']), should_stop=lambda: stopped)
        self.assertTrue(closed)
        self.assertEqual(len(result.pending), 1)
        self.assertFalse(result.complete)
        self.assertIn('Stopped by you', result.stop_reason)
        self.assertEqual(result.analyses, [])

    def test_missing_model_digest_does_not_reuse_unidentified_weights(self):
        self.client.list.return_value.models[0].digest = None
        reviews, cache = make_reviews(["Cold coffee."]), {}
        analyze_reviews(reviews, cache=cache)
        result = analyze_reviews(reviews, cache=cache)
        self.assertEqual(self.client.chat.call_count, 2)
        self.assertEqual(cache, {})
        self.assertEqual(result.reused_reviews, 0)


class WeeklyReportTests(unittest.TestCase):
    def test_reporting_week_uses_monday_through_sunday_including_year_boundary(self):
        self.assertEqual(reporting_week(date(2026, 11, 4)), (date(2026, 11, 2), date(2026, 11, 8)))
        self.assertEqual(reporting_week(date(2026, 11, 8)), (date(2026, 11, 2), date(2026, 11, 8)))
        self.assertEqual(reporting_week(date(2026, 12, 31)), (date(2026, 12, 28), date(2027, 1, 3)))

    def test_download_labels_selected_period_and_does_not_claim_verified_dates(self):
        result = BatchResult([Analysis(Review(1, "Friendly staff."), Extraction(
            positives=["Friendly staff."], complaints=[],
        ))], 0.2, "fixture")
        report = render_report(result, reporting_day=date(2026, 11, 4))
        self.assertIn("REVIEWWISE WEEKLY FEEDBACK REPORT", report)
        self.assertIn("02 Nov 2026 - 08 Nov 2026 (selected by you)", report)
        self.assertIn("input dates are not verified or filtered", report)


class CountingTests(unittest.TestCase):
    def test_m2_reference_counts_given_correct_extraction_labels(self):
        # This isolates counting; it does NOT test whether a real model produces these labels.
        texts = json.loads((ROOT / "experiments/reviews.json").read_text(encoding="utf-8"))
        expected = {
            "slow_service": [1, 6, 8], "cold_coffee": [4, 10], "high_prices": [7, 10],
            "dirty_tables": [5], "incorrect_order": [3], "unfriendly_staff": [9],
        }
        analyses = []
        for number, text in enumerate(texts, 1):
            complaints = [
                {"category": category, "quote": text}
                for category, ids in expected.items() if number in ids
            ]
            # Duplicate extraction of the same category must not inflate counts.
            analyses.append(Analysis(Review(number, text), Extraction(positives=[], complaints=complaints * 2)))
        rows = {row["category"]: row for row in complaint_rows(analyses)}
        for category, numbers in expected.items():
            self.assertEqual(rows[category]["Reviews"], len(numbers))
            self.assertEqual(rows[category]["Review numbers"], ", ".join(map(str, numbers)))
        report = render_report(BatchResult(analyses, 1.25, "test-fixture"))
        self.assertIn("Slow service: 3 review(s); reviews 1, 6, 8", report)
        self.assertEqual(len(suggested_actions(analyses)), 3)

    def test_positive_only_input_does_not_invent_complaints_or_actions(self):
        analyses = [Analysis(Review(1, "Excellent coffee!"), Extraction(positives=["Excellent coffee!"], complaints=[]))]
        self.assertEqual(complaint_rows(analyses), [])
        self.assertEqual(suggested_actions(analyses), [])
        self.assertIn("No complaints extracted", render_report(BatchResult(analyses, 0.1, "test")))

    def test_other_feedback_does_not_become_a_fabricated_specific_action(self):
        analyses = [Analysis(Review(1, "Too noisy."), Extraction(
            positives=[], complaints=[{"category": "other", "quote": "Too noisy."}],
        ))]
        self.assertEqual(complaint_rows(analyses)[0]["Reviews"], 1)
        self.assertEqual(suggested_actions(analyses), [])
