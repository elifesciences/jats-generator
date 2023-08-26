# coding=utf-8

import unittest
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
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


class TestAppendToTag(unittest.TestCase):
    "tests for utils.append_to_tag()"

    def test_append_to_tag(self):
        parent = Element("body")
        tag_name = "sec"
        original_string = '<p id="test">A <italic>test</italic>,<break/> here &>.</p>'
        namespace_map = None
        attributes = ["id"]
        attributes_text = 'id="s1"'
        expected = (
            b"<body>"
            b'<sec id="s1">'
            b'<p id="test">A <italic>test</italic>,<break /> here &amp;&gt;.</p>'
            b"</sec>"
            b"</body>"
        )
        result = utils.append_to_tag(
            parent,
            tag_name,
            original_string,
            namespace_map=namespace_map,
            attributes=attributes,
            attributes_text=attributes_text,
        )
        self.assertEqual(ElementTree.tostring(result), expected)
