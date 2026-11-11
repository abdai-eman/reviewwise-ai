"""Exercise actual worker concurrency and cancellation without model inference."""
from dataclasses import replace
from threading import Event
import unittest
from unittest.mock import patch

from reviewwise.jobs import is_busy, start_job
from reviewwise.pipeline import Analysis, BatchResult, Extraction, Review, ReviewWiseError


class JobTests(unittest.TestCase):
    def test_live_results_survive_cancellation_and_a_second_analysis_is_rejected(self):
        entered, release = Event(), Event()
        reviews = [Review(1, 'Cold coffee.'), Review(2, 'Slow service.')]
        partial = BatchResult([Analysis(reviews[0], Extraction(positives=[], complaints=[{'category': 'cold_coffee', 'quote': 'Cold coffee.'}]))],
                              .1, 'fixture', pending=[reviews[1]], running=True)

        def work(items, cache, on_update, should_stop):
            on_update(partial)
            entered.set()
            if not release.wait(3):
                raise AssertionError('Worker test did not release its gate')
            return replace(partial, running=False, stop_reason='Stopped by you.' if should_stop() else '')

        with patch('reviewwise.pipeline.analyze_reviews', side_effect=work):
            job = start_job(reviews, {})
            try:
                self.assertTrue(entered.wait(2))
                self.assertTrue(is_busy())
                self.assertEqual(len(job.snapshot()[0].analyses), 1)
                with self.assertRaisesRegex(ReviewWiseError, 'Another report'):
                    start_job(reviews, {})
                job.cancel()
            finally:
                release.set()
                job.thread.join(3)
            result, error, _, running, _ = job.snapshot()
            self.assertIsNone(error)
            self.assertFalse(running)
            self.assertFalse(is_busy())
            self.assertEqual(len(result.analyses), 1)
            self.assertEqual(len(result.pending), 1)
            self.assertIn('Stopped by you', result.stop_reason)
