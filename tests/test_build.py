import unittest
import os
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
from elifearticle.article import Article, RelatedArticle
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


class TestSetTitleGroup(unittest.TestCase):
    def test_set_title_group(self):
        "test title-group and article-title tag"
        root = Element("root")
        article = Article(None, "Title")
        build.set_title_group(root, article)
        xml_string = ElementTree.tostring(root, encoding="utf-8")
        expected = b"<root><title-group><article-title>Title</article-title></title-group></root>"
        self.assertEqual(xml_string, expected)


class TestSetArticleId(unittest.TestCase):
    def test_set_article_id(self):
        "test setting article-id tag with doi value"
        root = Element("root")
        article = Article("10.7554/eLife.00666", "Title")
        build.set_article_id(root, article)
        xml_string = ElementTree.tostring(root, encoding="utf-8")
        expected = b'<root><article-id pub-id-type="doi">10.7554/eLife.00666</article-id></root>'
        self.assertEqual(xml_string, expected)


class TestSetRelatedObject(unittest.TestCase):
    def test_set_related_object(self):
        "test setting article-id tag with doi value"
        root = Element("root")
        article = Article("10.7554/eLife.00666.sa0", "Evaluation summary")
        article.id = "sa0"
        related_article = RelatedArticle()
        related_article.ext_link_type = "continued-by"
        related_article.xlink_href = (
            "https://sciety.org/articles/activity/10.1101/2021.11.09.467796"
        )
        article.related_articles = [related_article]

        build.set_related_object(root, article)
        xml_string = ElementTree.tostring(root, encoding="utf-8")
        expected = (
            b"<root>"
            b'<related-object id="sa0ro1" object-id-type="id" '
            b'object-id="10.1101/2021.11.09.467796" link-type="continued-by" '
            b'xlink:href="https://sciety.org/articles/activity/10.1101/2021.11.09.467796" />'
            b"</root>"
        )
        self.assertEqual(xml_string, expected)
