"""IDs must resolve to real original evidence, independently of AI accuracy."""
import json
import unittest
from pydantic import ValidationError
from reviewwise.evidence import decode_packet, evidence_units
from reviewwise.pipeline import Review


class EvidenceTests(unittest.TestCase):
    def test_positive_and_complaint_ids_copy_exact_multilingual_original_units(self):
        cases = [
            'The staff were friendly but the coffee was cold.',
            'Le personnel était agréable mais le café était froid.',
            'Das Personal war freundlich, aber der Kaffee war kalt.',
            "D'Personal war flott mee de Kaffi war kal.",
        ]
        for text in cases:
            with self.subTest(text=text):
                units = evidence_units(text)
                self.assertEqual(len(units), 2)
                payload = json.dumps({'results': [{'id': 1, 'positive': [0], 'complaints': [{'unit': 1, 'category': 'cold_coffee'}]}]})
                output = decode_packet(payload, [Review(1, text)])[1]
                self.assertEqual(output['positives'], [units[0]])
                self.assertEqual(output['complaints'][0]['quote'], units[1])
                self.assertIn(units[0], text)
                self.assertIn(units[1], text)

    def test_missing_duplicate_unknown_review_ids_and_invalid_evidence_are_rejected(self):
        valid = {'id': 1, 'positive': [], 'complaints': [{'unit': 0, 'category': 'cold_coffee'}]}
        invalid = [
            [], [valid, valid], [{**valid, 'id': 2}],
            [{**valid, 'positive': [-1]}],
            [{**valid, 'complaints': [{'unit': 99, 'category': 'cold_coffee'}]}],
            [{**valid, 'complaints': [{'unit': 0, 'category': 'invented'}]}],
        ]
        for entries in invalid:
            with self.subTest(entries=entries), self.assertRaises((ValueError, ValidationError)):
                decode_packet(json.dumps({'results': entries}), [Review(1, 'Cold coffee.')])
