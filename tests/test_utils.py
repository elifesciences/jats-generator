# coding=utf-8

import unittest
from jatsgenerator import utils


class TestObjectIdFromUri(unittest.TestCase):
    def test_object_id_from_uri(self):
        passes = [
            {
                "uri": None,
                "expected": None,
            },
            {
                "uri": "https://sciety.org/articles/activity/10.1101/865006",
                "expected": "10.1101/865006",
            },
            {
                "uri": "https://example.org/10/1101/865006",
                "expected": "https://example.org/10/1101/865006",
            },
            {
                "uri": "https://example.org/10.1101/10.865006",
                "expected": "10.1101/10.865006",
            },
        ]
        for test_data in passes:
            self.assertEqual(
                utils.object_id_from_uri(test_data.get("uri")),
                test_data.get("expected"),
            )
