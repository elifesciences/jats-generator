import unittest
import time
import sys
from mock import Mock, patch
from elifearticle.article import (
    Affiliation,
    Article,
    ArticleDate,
    ContentBlock,
    Contributor,
    Event,
    License,
    RelatedArticle,
    Role,
)
from ejpcsvparser import csv_data
from jatsgenerator import generate
from jatsgenerator.generate import ArticleXML
from tests import helpers


def anonymous_contributor(contrib_type="author"):
    "instantiate an anonymous Contributor object"
    contributor = Contributor(contrib_type, None, None)
    contributor.anonymous = True
    return contributor


class TestGenerate(unittest.TestCase):
    def setUp(self):
        # override settings
        csv_data.CSV_PATH = helpers.TEST_DATA_PATH
        self.passes = []
        self.default_pub_date = time.strptime("2012-11-13", "%Y-%m-%d")
        self.passes.append(
            (3, "elife", self.default_pub_date, 1, "elife_poa_e00003.xml")
        )
        self.passes.append((7, "elife", None, None, "elife_poa_e00007.xml"))
        self.passes.append((12, "elife", None, None, "elife_poa_e00012.xml"))
        self.passes.append((2725, "elife", None, None, "elife_poa_e02725.xml"))
        self.passes.append((2935, "elife", None, None, "elife_poa_e02935.xml"))
        self.passes.append((12717, "elife", None, None, "elife_poa_e12717.xml"))
        self.passes.append((14874, "elife", None, None, "elife_poa_e14874.xml"))
        self.passes.append((14997, "elife", None, None, "elife_poa_e14997.xml"))
        self.passes.append((21598, "elife", None, None, "elife_poa_e21598.xml"))
        self.passes.append((65697, "elife", None, None, "elife_poa_e65697.xml"))

    def test_build_xml_from_csv(self):
        "set of tests building csv into xml and compare the output"
        for (
            article_id,
            config_section,
            pub_date,
            volume,
            expected_xml_file,
        ) in self.passes:
            jats_config = helpers.build_config(config_section)
            article = generate.build_article_from_csv(article_id, jats_config)
            self.assertIsNotNone(article, "count not build article from csv")
            # add the pub_date
            if pub_date:
                pub_date_object = ArticleDate("pub", pub_date)
                article.add_date(pub_date_object)
            # set the volume
            if volume:
                article.volume = volume
            # generate XML
            xml_return_value = generate.build_xml_to_disk(
                article_id, article, jats_config, add_comment=False
            )
            self.assertTrue(
                xml_return_value,
                "could not generate xml to disk for {article_id}".format(
                    article_id=article_id
                ),
            )
            generated_xml = helpers.read_file_content(
                helpers.TARGET_OUTPUT_DIR + expected_xml_file
            )
            model_xml = helpers.read_file_content(
                helpers.TEST_DATA_PATH + expected_xml_file
            )
            if sys.version_info < (3, 8):
                # pre-Python 3.8 the order of XML tag attributes are alphabetised
                # research-article
                model_xml = model_xml.replace(
                    b'<article xmlns:mml="http://www.w3.org/1998/Math/MathML" xmlns:xlink="http://www.w3.org/1999/xlink" article-type="research-article" dtd-version="1.1d3">',
                    b'<article article-type="research-article" dtd-version="1.1d3" xmlns:mml="http://www.w3.org/1998/Math/MathML" xmlns:xlink="http://www.w3.org/1999/xlink">',
                )
                # discussion
                model_xml = model_xml.replace(
                    b'<article xmlns:mml="http://www.w3.org/1998/Math/MathML" xmlns:xlink="http://www.w3.org/1999/xlink" article-type="discussion" dtd-version="1.1d3">',
                    b'<article article-type="discussion" dtd-version="1.1d3" xmlns:mml="http://www.w3.org/1998/Math/MathML" xmlns:xlink="http://www.w3.org/1999/xlink">',
                )
            self.assertEqual(generated_xml, model_xml)

    def test_build_article_from_csv_failure(self):
        "test when an article fails to be built"
        article_id = 99999
        return_value = generate.build_article_from_csv(article_id)
        self.assertFalse(return_value)

    def test_build_xml_failure(self):
        "test when article xml to be built"
        article_id = 99999
        return_value = generate.build_xml(article_id)
        self.assertIsNone(return_value)

    def test_build_xml_failure_bad_article(self):
        "test building article xml from a bad article object"
        article_id = 99999
        article = True
        article_xml = generate.build_xml(article_id, article)
        self.assertFalse(hasattr(article_xml, "root"))

    def test_article_xml_instantiate_failure(self):
        "test ArticleXML object with bad data"
        article_xml = ArticleXML(None, None)
        self.assertFalse(hasattr(article_xml, "root"))

    @patch("jatsgenerator.generate.write_xml_to_disk")
    def test_build_xml_to_disk_failure(self, fake_writer):
        fake_writer.side_effect = IOError(Mock())
        article_id = 7
        return_value = generate.build_xml_to_disk(article_id)
        self.assertFalse(return_value)
        # second failure for no article built
        article_id = 99999
        return_value = generate.build_xml_to_disk(article_id)
        self.assertFalse(return_value)

    def test_build_no_conflict_default(self):
        """ "
        test building with no article conflict_default value for test coverage
        and also test pretty output too for coverage
        """
        # one of the authors in 7 has a conflict, will trigger testing the line of code
        article_id = 7
        article = generate.build_article_from_csv(article_id)
        # reset the conflict default
        article.conflict_default = None
        article_xml = generate.build_xml(article_id, article)
        self.assertIsNotNone(article_xml, "count not generate xml for the article")
        self.assertFalse(
            "other authors declare that no competing interests exist"
            in article_xml.output_xml(pretty=True, indent="\t").decode("utf8")
        )

    def test_set_copyright_authors(self):
        "start with an article then change the authors for test coverage for different input"
        article_id = 7
        article = generate.build_article_from_csv(article_id)
        # test the value as is with more than two authors
        article_xml = generate.build_xml(article_id, article)
        self.assertTrue(
            "<copyright-holder>Schuman et al</copyright-holder>"
            in article_xml.output_xml().decode("utf8")
        )
        # set authors to be exactly two
        for index in range(len(article.contributors) - 1):
            if index > 1:
                del article.contributors[index]
        article_xml = generate.build_xml(article_id, article)
        self.assertTrue(
            "<copyright-holder>Schuman &amp; Barthel</copyright-holder>"
            in article_xml.output_xml().decode("utf8")
        )
        # set authors to be exactly one
        for index in range(len(article.contributors) - 1):
            if index > 0:
                del article.contributors[index]
        article_xml = generate.build_xml(article_id, article)
        self.assertTrue(
            "<copyright-holder>Schuman</copyright-holder>"
            in article_xml.output_xml().decode("utf8")
        )
        # no authors
        article.contributors = []
        article_xml = generate.build_xml(article_id, article)
        self.assertTrue(
            "<copyright-holder/>" in article_xml.output_xml().decode("utf8")
        )

    def test_set_copyright_license_date(self):
        "start with an article then remove the license date"
        article_id = 7
        article = generate.build_article_from_csv(article_id)
        # remove the license date
        if article.dates.get("license"):
            del article.dates["license"]
        # change the accepted date just to be sure
        accepted_date = time.strptime("2037-11-13", "%Y-%m-%d")
        accepted_date_object = ArticleDate("pub", accepted_date)
        article.dates["accepted"] = accepted_date_object
        article_xml = generate.build_xml(article_id, article)
        self.assertTrue(
            "<copyright-year>2037</copyright-year>"
            in article_xml.output_xml().decode("utf8")
        )

    def test_contributor_equal_contrib(self):
        "set equal_contrib on an author to test the output"
        article_id = 7
        article = generate.build_article_from_csv(article_id)
        # set all the authors as equal contributors
        for author in article.contributors:
            if author.contrib_type == "author":
                author.equal_contrib = True
        article_xml = generate.build_xml(article_id, article)
        self.assertTrue(
            '<contrib contrib-type="author" equal_contrib="yes" id="author-1399">'
            in article_xml.output_xml().decode("utf8")
        )
        self.assertTrue(
            '<contrib contrib-type="author" corresp="yes" equal_contrib="yes" id="author-1400">'
            in article_xml.output_xml().decode("utf8")
        )
        self.assertTrue(
            '<contrib contrib-type="author" corresp="yes" equal_contrib="yes" id="author-1013">'
            in article_xml.output_xml().decode("utf8")
        )

    def test_contributor_phone_fax(self):
        "set phone and fax on an author to test the output for test coverage"
        article_id = 7
        article = generate.build_article_from_csv(article_id)
        # set all the authors as equal contributors
        article.contributors[0].affiliations[0].phone = "555-5555"
        article.contributors[0].affiliations[0].fax = "555-5555"
        article_xml = generate.build_xml(article_id, article)
        self.assertTrue(
            "<phone>555-5555</phone>" in article_xml.output_xml().decode("utf8")
        )
        self.assertTrue(
            "<fax>555-5555</fax>" in article_xml.output_xml().decode("utf8")
        )

    def test_do_display_channel(self):
        "test when the display channel is blank"
        article_id = 7
        article = generate.build_article_from_csv(article_id)
        article.display_channel = None
        article_xml = generate.build_xml(article_id, article)
        self.assertTrue(
            '<subj-group subj-group-type="display-channel">'
            not in article_xml.output_xml().decode("utf8")
        )

    def test_do_subject_heading(self):
        "test when the article_categories is empty"
        article_id = 7
        article = generate.build_article_from_csv(article_id)
        article.article_categories = []
        article_xml = generate.build_xml(article_id, article)
        self.assertTrue(
            '<subj-group subj-group-type="heading">'
            not in article_xml.output_xml().decode("utf8")
        )

    def test_do_article_categories(self):
        "test when there is no display channel or article categories"
        article_id = 7
        article = generate.build_article_from_csv(article_id)
        article.display_channel = None
        article.article_categories = []
        article_xml = generate.build_xml(article_id, article)
        # now it should have no <article-categories> section at all
        self.assertTrue(
            "<article-categories>" not in article_xml.output_xml().decode("utf8")
        )


class TestGeneratePreprint(unittest.TestCase):
    def test_preprint(self):
        "test from Article objects to generate an XML for a preprint article"
        jats_config = helpers.build_config("elife_preprint")
        add_comment = False
        # build Article objects
        article = Article(
            "10.7554/eLife.84364",
            (
                "Opto-RhoGEFs: an optimized optogenetic toolbox to reversibly control "
                "Rho GTPase activity on a global to subcellular scale, enabling "
                "precise control over vascular endothelial barrier strength"
            ),
        )
        article.article_type = "preprint"
        article.manuscript = "84364"
        article.version_doi = "10.7554/eLife.84364.1"
        article.abstract = "An abstract."
        # contributor
        contributor = Contributor("author", "Mahlandt", "Eike K.")
        affiliation = Affiliation()
        affiliation.institution = (
            "Swammerdam Institute for Life Sciences, Section of Molecular Cytology, "
            "van Leeuwenhoek Centre for Advanced Microscopy, University of Amsterdam, "
            "Science Park 904, 1098 XH, Amsterdam"
        )
        affiliation.country = "The Netherlands"
        contributor.set_affiliation(affiliation)
        article.add_contributor(contributor)
        # date
        article.add_date(
            ArticleDate("posted_date", time.strptime("2023-02-13", "%Y-%m-%d"))
        )
        # volume
        article.volume = 12
        # license
        license_object = License()
        license_object.href = "http://creativecommons.org/licenses/by/4.0/"
        article.license = license_object
        # pub-history
        preprint_event = Event()
        preprint_event.event_type = "preprint"
        preprint_event.date = time.strptime("2022-10-17", "%Y-%m-%d")
        preprint_event.uri = "https://doi.org/10.1101/2022.10.17.512253"
        reviewed_preprint_event = Event()
        reviewed_preprint_event.event_type = "reviewed-preprint"
        reviewed_preprint_event.date = time.strptime("2023-02-12", "%Y-%m-%d")
        reviewed_preprint_event.uri = "https://doi.org/10.7554/eLife.84364.1"
        article.publication_history = [preprint_event, reviewed_preprint_event]
        # sub-article data
        sub_article_1 = Article("10.7554/eLife.84364.1.sa0", "eLife assessment")
        sub_article_1.id = "sa0"
        sub_article_1.article_type = "editor-report"
        affiliation = Affiliation()
        affiliation.institution = "University of California"
        affiliation.city = "Berkeley"
        affiliation.country = "United States"
        contributor = Contributor("author", "Eisen", "Michael B")
        contributor.set_affiliation(affiliation)
        sub_article_1.add_contributor(contributor)

        sub_article_2 = Article(
            "10.7554/eLife.84364.1.sa1", "Reviewer #1 (Public Review)"
        )
        sub_article_2.id = "sa1"
        sub_article_2.article_type = "referee-report"
        sub_article_2.add_contributor(anonymous_contributor())

        sub_article_3 = Article(
            "10.7554/eLife.84364.1.sa2", "Reviewer #2 (Public Review)"
        )
        sub_article_3.id = "sa2"
        sub_article_3.article_type = "referee-report"
        sub_article_3.add_contributor(anonymous_contributor())

        sub_article_4 = Article(
            "10.7554/eLife.84364.1.sa3", "Reviewer #3 (Public Review)"
        )
        sub_article_4.id = "sa3"
        sub_article_4.article_type = "referee-report"
        sub_article_4.add_contributor(anonymous_contributor())

        sub_article_5 = Article("10.7554/eLife.84364.1.sa4", "Author response")
        sub_article_5.id = "sa4"
        sub_article_5.article_type = "author-comment"
        contributor = Contributor("author", "Mahlandt", "Eike K.")
        sub_article_5.add_contributor(contributor)

        article.review_articles = [
            sub_article_1,
            sub_article_2,
            sub_article_3,
            sub_article_4,
            sub_article_5,
        ]
        # invoke
        article_xml = generate.ArticleXML(article, jats_config, add_comment)
        xml_string = article_xml.output_xml(pretty=True, indent="\t")
        # assertion
        model_xml = helpers.read_file_content(helpers.TEST_DATA_PATH + "preprint.xml")
        self.assertEqual(xml_string, model_xml)
