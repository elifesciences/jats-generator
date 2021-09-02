import unittest
import os
from ejpcsvparser import csv_data
from jatsgenerator import generate, build

TEST_BASE_PATH = os.path.dirname(os.path.abspath(__file__)) + os.sep
TEST_DATA_PATH = TEST_BASE_PATH + "test_data" + os.sep


class TestBuild(unittest.TestCase):
    def setUp(self):
        # override settings
        csv_data.CSV_PATH = TEST_DATA_PATH

    def test_author_keywords(self):
        "test setting author keywords which is currently disabled"
        article_id = 7
        article = generate.build_article_from_csv(article_id)
        article.display_channel = None
        article.article_categories = []
        article_xml = generate.build_xml(article_id, article)
        front = article_xml.set_frontmatter(article_xml.root, article)
        article_meta = article_xml.set_article_meta(front, article)
        build.set_kwd_group_author_keywords(article_meta, article)
        self.assertTrue(
            '<kwd-group kwd-group-type="author-keywords">'
            in article_xml.output_xml().decode("utf8")
        )
