"""Local persistence must preserve evidence and clearly account for missing reviews."""
from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from reviewwise.pipeline import Analysis, BatchResult, Extraction, FailedReview, Review, complaint_rows
from reviewwise.storage import ReportStore, load_report, report_document


def fixture():
    return BatchResult([Analysis(Review(1, 'Le café était froid.'), Extraction(positives=[], complaints=[{'category':'cold_coffee','quote':'Le café était froid.'}]))], .5, 'storage-test-fixture')


class StorageTests(unittest.TestCase):
    def test_save_and_reopen_preserve_original_evidence_without_ai(self):
        with TemporaryDirectory() as directory:
            store = ReportStore(directory)
            document = report_document(fixture(), date(2026, 11, 5))
            name = store.save(document)
            entries = store.list()
            self.assertEqual(entries[0][0], name)
            self.assertEqual(entries[0][1].result.analyses[0].review.text, 'Le café était froid.')
            self.assertEqual(complaint_rows(entries[0][1].result.analyses)[0]['Reviews'], 1)

    def test_partial_snapshot_stays_partial_after_reopening(self):
        result = fixture()
        result = BatchResult(result.analyses, .5, 'fixture', failures=[FailedReview(Review(2, 'Bad order.'), 'fixture failure')], pending=[Review(3, 'Slow service.')], running=True)
        document = report_document(result, date(2026, 11, 5))
        loaded = load_report(document.model_dump_json()).result
        self.assertFalse(loaded.complete)
        self.assertFalse(loaded.running)
        self.assertEqual(loaded.total_reviews, 3)
        self.assertEqual(len(loaded.analyses), 1)

    def test_invented_evidence_and_overlapping_coverage_are_rejected(self):
        original = json.loads(report_document(fixture(), date(2026,11,5)).model_dump_json())
        forged = json.loads(json.dumps(original))
        forged['result']['analyses'][0]['extraction']['complaints'][0]['quote'] = 'Invented words'
        with self.assertRaises(ValueError):
            load_report(json.dumps(forged))
        original['result']['pending'] = [{'number':1,'text':'Duplicate input'}]
        with self.assertRaises(ValueError):
            load_report(json.dumps(original))

    def test_supplied_counts_are_not_trusted_and_delete_cannot_escape_store(self):
        data = json.loads(report_document(fixture(),date(2026,11,5)).model_dump_json())
        data['counts'] = {'cold_coffee':9999}
        loaded = load_report(json.dumps(data))
        self.assertEqual(complaint_rows(loaded.result.analyses)[0]['Reviews'],1)
        with TemporaryDirectory() as directory:
            root=Path(directory)
            outside=root/'outside.json'
            outside.write_text('keep')
            store=ReportStore(root/'reports')
            name=store.save(loaded)
            with self.assertRaises(ValueError):store.delete('../outside.json')
            self.assertEqual(outside.read_text(),'keep')
            store.delete(name)
            self.assertEqual(store.list(),[])
