import unittest
import time
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
from elifearticle.article import (
    Affiliation,
    Article,
    ContentBlock,
    Contributor,
    Event,
    RelatedArticle,
    Role,
)
from ejpcsvparser import csv_data
from jatsgenerator import generate, build
from tests import helpers


class TestBuild(unittest.TestCase):
    def setUp(self):
        # override settings
        csv_data.CSV_PATH = helpers.TEST_DATA_PATH

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


class TestSetContribName(unittest.TestCase):
    def test_set_contrib_name_anonymous(self):
        root = Element("root")
        contributor = Contributor("author", None, None)
        contributor.anonymous = True
        build.set_contrib_name(root, contributor)
        xml_string = ElementTree.tostring(root, encoding="utf-8")
        expected = b"<root><anonymous /></root>"
        self.assertEqual(xml_string, expected)

    def test_set_contrib_name_collab(self):
        root = Element("root")
        contributor = Contributor("author", None, None, "Orgname")
        build.set_contrib_name(root, contributor)
        xml_string = ElementTree.tostring(root, encoding="utf-8")
        expected = b"<root><collab>Orgname</collab></root>"
        self.assertEqual(xml_string, expected)

    def test_set_contrib_name(self):
        root = Element("root")
        contributor = Contributor("author", "Surname", "Given")
        build.set_contrib_name(root, contributor)
        xml_string = ElementTree.tostring(root, encoding="utf-8")
        expected = (
            b"<root>"
            b"<name>"
            b"<surname>Surname</surname>"
            b"<given-names>Given</given-names>"
            b"</name>"
            b"</root>"
        )
        self.assertEqual(xml_string, expected)


class TestSetContribRole(unittest.TestCase):
    def test_set_set_contrib_role(self):
        "older logic for hard-coded Reviewing editor role"
        root = Element("root")
        contrib_type = "editor"
        contributor = Contributor(contrib_type, None, None)
        build.set_contrib_role(root, contrib_type)
        xml_string = ElementTree.tostring(root, encoding="utf-8")
        expected = b"<root><role>Reviewing editor</role></root>"
        self.assertEqual(xml_string, expected)

    def test_set_set_contrib_role_from_contributor(self):
        "newer logic takes role from the Contributor.roles"
        root = Element("root")
        contrib_type = "author"
        contributor = Contributor(contrib_type, None, None)
        contributor.anonymous = True
        contributor.roles = [Role("Reviewer", "referee")]
        build.set_contrib_role(root, contrib_type, contributor)
        xml_string = ElementTree.tostring(root, encoding="utf-8")
        expected = b'<root><role specific-use="referee">Reviewer</role></root>'
        self.assertEqual(xml_string, expected)


class TestSetContribOrcid(unittest.TestCase):
    def test_set_contrib_orcid_true(self):
        root = Element("root")
        contributor = Contributor("author", "Surname", "Given")
        contributor.orcid = "0000-00000-0000-0000"
        contributor.orcid_authenticated = True
        build.set_contrib_orcid(root, contributor)
        xml_string = ElementTree.tostring(root, encoding="utf-8")
        expected = (
            b"<root>"
            b'<contrib-id authenticated="true" contrib-id-type="orcid">'
            b"http://orcid.org/0000-00000-0000-0000"
            b"</contrib-id>"
            b"</root>"
        )
        self.assertEqual(xml_string, expected)

    def test_not_authenticated(self):
        "test if ORCID is not authenticated"
        root = Element("root")
        contributor = Contributor("author", "Surname", "Given")
        contributor.orcid = "0000-00000-0000-0000"
        build.set_contrib_orcid(root, contributor)
        xml_string = ElementTree.tostring(root, encoding="utf-8")
        expected = (
            b"<root>"
            b'<contrib-id contrib-id-type="orcid">'
            b"http://orcid.org/0000-00000-0000-0000"
            b"</contrib-id>"
            b"</root>"
        )
        self.assertEqual(xml_string, expected)

    def test_orcid_url(self):
        "test if ORCID is a URL value"
        root = Element("root")
        contributor = Contributor("author", "Surname", "Given")
        contributor.orcid = "https://orcid.org/0000-00000-0000-0000"
        build.set_contrib_orcid(root, contributor)
        xml_string = ElementTree.tostring(root, encoding="utf-8")
        expected = (
            b"<root>"
            b'<contrib-id contrib-id-type="orcid">'
            b"http://orcid.org/0000-00000-0000-0000"
            b"</contrib-id>"
            b"</root>"
        )
        self.assertEqual(xml_string, expected)


class TestSetAff(unittest.TestCase):
    def setUp(self):
        self.affiliation = Affiliation()
        self.affiliation.phone = "Phone"
        self.affiliation.fax = "Fax"
        self.affiliation.department = "Department"
        self.affiliation.institution = "Institution"
        self.affiliation.city = "City"
        self.affiliation.country = "Country"
        self.affiliation.ror = "ror"

    def test_set_aff_minimal(self):
        "minimal affiliation data"
        root = Element("root")
        contrib_type = "author"
        build.set_aff(root, Affiliation(), contrib_type)
        xml_string = ElementTree.tostring(root, encoding="utf-8")
        expected = b"<root><aff /></root>"
        self.assertEqual(xml_string, expected)

    def test_set_aff_default(self):
        "default, older, style with some comma separated tags"
        root = Element("root")
        contrib_type = "author"
        aff_id = "1"
        build.set_aff(root, self.affiliation, contrib_type, aff_id)
        xml_string = ElementTree.tostring(root, encoding="utf-8")
        expected = (
            b"<root>"
            b'<aff id="1">'
            b'<institution-id institution-id="ror">ror</institution-id>'
            b'<institution content-type="dept">Department</institution>, '
            b"<institution>Institution</institution>, "
            b"<addr-line>"
            b'<named-content content-type="city">City</named-content>'
            b"</addr-line>, "
            b"<country>Country</country>"
            b"<phone>Phone</phone>"
            b"<fax>Fax</fax>"
            b"</aff>"
            b"</root>"
        )
        self.assertEqual(xml_string, expected)

    def test_set_aff_default_editor(self):
        "default, editor style does not add department for some reason"
        root = Element("root")
        contrib_type = "editor"
        aff_id = "1"
        build.set_aff(root, self.affiliation, contrib_type, aff_id)
        xml_string = ElementTree.tostring(root, encoding="utf-8")
        expected = (
            b"<root>"
            b'<aff id="1"><institution-id institution-id="ror">ror</institution-id>'
            b"<institution>Institution</institution>, "
            b"<addr-line>"
            b'<named-content content-type="city">City</named-content>'
            b"</addr-line>, "
            b"<country>Country</country>"
            b"<phone>Phone</phone>"
            b"<fax>Fax</fax>"
            b"</aff>"
            b"</root>"
        )
        self.assertEqual(xml_string, expected)

    def test_set_aff_newer_style(self):
        "do not add tag tail and add institution-wrap tag"
        root = Element("root")
        contrib_type = "author"
        aff_id = "1"
        tail = None
        institution_wrap = True
        build.set_aff(
            root, self.affiliation, contrib_type, aff_id, tail, institution_wrap
        )
        xml_string = ElementTree.tostring(root, encoding="utf-8")
        expected = (
            b"<root>"
            b'<aff id="1">'
            b"<institution-wrap>"
            b'<institution-id institution-id="ror">ror</institution-id>'
            b'<institution content-type="dept">Department</institution>'
            b"<institution>Institution</institution>"
            b"</institution-wrap>"
            b"<addr-line>"
            b'<named-content content-type="city">City</named-content>'
            b"</addr-line>"
            b"<country>Country</country>"
            b"<phone>Phone</phone>"
            b"<fax>Fax</fax>"
            b"</aff>"
            b"</root>"
        )
        self.assertEqual(xml_string, expected)


class TestSetTitleGroup(unittest.TestCase):
    def test_set_title_group(self):
        "test title-group and article-title tag"
        root = Element("root")
        article = Article(None, "Title")
        build.set_title_group(root, article)
        xml_string = ElementTree.tostring(root, encoding="utf-8")
        expected = b"<root><title-group><article-title>Title</article-title></title-group></root>"
        self.assertEqual(xml_string, expected)


class TestSetPublicationHistory(unittest.TestCase):
    def test_set_publication_history(self):
        "set pub-history tag and event tag inside"
        root = Element("root")
        article = Article(None, "Title")
        preprint_event = Event()
        preprint_event.event_type = "preprint"
        preprint_event.event_desc = "This manuscript was published as a preprint."
        preprint_event.date = time.strptime("2022-10-17", "%Y-%m-%d")
        preprint_event.uri = "https://doi.org/10.1101/2022.10.17.512253"
        article.publication_history = [preprint_event]
        expected = (
            b"<root>"
            b"<pub-history>"
            b"<event>"
            b"<event-desc>This manuscript was published as a preprint.</event-desc>"
            b'<date date-type="preprint" iso-8601-date="2022-10-17">'
            b"<day>17</day>"
            b"<month>10</month>"
            b"<year>2022</year>"
            b"</date>"
            b'<self-uri content-type="preprint" xlink:href="https://doi.org/10.1101/2022.10.17.512253" />'
            b"</event>"
            b"</pub-history>"
            b"</root>"
        )
        # invoke
        build.set_publication_history(root, article)
        xml_string = ElementTree.tostring(root, encoding="utf-8")
        self.assertEqual(xml_string, expected)


class TestSetSubArticle(unittest.TestCase):
    def test_set_sub_article(self):
        root = Element("root")
        sub_article = Article("10.7554/eLife.84364.1.sa0", "eLife assessment")
        sub_article.id = "sa0"
        sub_article.article_type = "editor-report"
        affiliation = Affiliation()
        affiliation.institution = "University of California"
        affiliation.city = "Berkeley"
        affiliation.country = "United States"
        contributor = Contributor("author", "Eisen", "Michael B")
        contributor.set_affiliation(affiliation)
        sub_article.add_contributor(contributor)
        expected = (
            b"<root>"
            b'<sub-article id="sa0" article-type="editor-report">'
            b"<front-stub>"
            b'<article-id pub-id-type="doi">10.7554/eLife.84364.1.sa0</article-id>'
            b"<title-group>"
            b"<article-title>eLife assessment</article-title>"
            b"</title-group>"
            b"<contrib-group>"
            b'<contrib contrib-type="author">'
            b"<name>"
            b"<surname>Eisen</surname>"
            b"<given-names>Michael B</given-names>"
            b"</name>"
            b"<aff>"
            b"<institution-wrap>"
            b"<institution>University of California</institution>, "
            b"</institution-wrap>"
            b"<addr-line>"
            b'<named-content content-type="city">Berkeley</named-content>'
            b"</addr-line>, "
            b"<country>United States</country>"
            b"</aff>"
            b"</contrib>"
            b"</contrib-group>"
            b"</front-stub>"
            b"</sub-article>"
            b"</root>"
        )
        # invoke
        build.set_sub_article(root, sub_article)
        xml_string = ElementTree.tostring(root, encoding="utf-8")

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


class TestSetBody(unittest.TestCase):
    def test_set_body(self):
        "test body tag with article content"
        root = Element("root")
        article = Article()
        article.content_blocks = [ContentBlock("p", "Test.")]

        build.set_body(root, article)
        xml_string = ElementTree.tostring(root, encoding="utf-8")
        expected = b"<root><body><p>Test.</p></body></root>"
        self.assertEqual(xml_string, expected)


class TestSetContentBlocks(unittest.TestCase):
    def test_set_content_blocks(self):
        root = Element("root")
        parent_block = ContentBlock("p", "First level paragraph.")
        child_block = ContentBlock("p", "", {"type": "empty"})
        parent_block.content_blocks.append(child_block)
        content_blocks = [parent_block]
        build.set_content_blocks(root, content_blocks)
        xml_string = ElementTree.tostring(root, encoding="utf-8")
        expected = b'<root><p>First level paragraph.<p type="empty" /></p></root>'
        self.assertEqual(xml_string, expected)

    def test_generate_max_level(self):
        "test exceeding the MAX_LEVEL of nested content"
        max_level_original = build.MAX_LEVEL
        build.MAX_LEVEL = 1
        # add two levels of nested content

        parent_block = ContentBlock("p", "First level paragraph.")
        child_block = ContentBlock("p", "Second level paragraph.")
        parent_block.content_blocks.append(child_block)
        content_blocks = [parent_block]
        root = Element("root")
        with self.assertRaises(Exception):
            build.set_content_blocks(root, content_blocks)
        # reset the module MAX_LEVEL value
        build.MAX_LEVEL = max_level_original
