import unittest
import time
import os
from mock import Mock, patch
from jatsgenerator import generate
from elifearticle.article import ArticleDate

TEST_BASE_PATH = os.path.dirname(os.path.abspath(__file__)) + os.sep
TEST_DATA_PATH = TEST_BASE_PATH + "test_data" + os.sep
TARGET_OUTPUT_DIR = TEST_BASE_PATH + "tmp" + os.sep
generate.settings.TARGET_OUTPUT_DIR = TARGET_OUTPUT_DIR

def read_file_content(file_name):
    fp = open(file_name, 'rb')
    content = fp.read()
    fp.close()
    return content

class TestGenerate(unittest.TestCase):

    def setUp(self):
        # override settings
        generate.data.CSV_PATH = 'tests/test_data/'
        self.passes = []
        self.default_pub_date = time.strptime("2012-11-13", "%Y-%m-%d")
        self.passes.append((3, 'elife', self.default_pub_date, 1, 'elife_poa_e00003.xml'))
        self.passes.append((7, 'elife', None, None, 'elife_poa_e00007.xml'))
        self.passes.append((12, 'elife', None, None, 'elife_poa_e00012.xml'))
        self.passes.append((2725, 'elife', None, None, 'elife_poa_e02725.xml'))
        self.passes.append((2935, 'elife', None, None, 'elife_poa_e02935.xml'))
        self.passes.append((12717, 'elife', None, None, 'elife_poa_e12717.xml'))
        self.passes.append((14874, 'elife', None, None, 'elife_poa_e14874.xml'))
        self.passes.append((14997, 'elife', None, None, 'elife_poa_e14997.xml'))
        self.passes.append((21598, 'elife', None, None, 'elife_poa_e21598.xml'))

    def test_build_xml_from_csv(self):
        "set of tests building csv into xml and compare the output"
        for (article_id, config_section, pub_date, volume, expected_xml_file) in self.passes:
            article = generate.build_article_from_csv(article_id, config_section)
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
                article_id, article, config_section, add_comment=False)
            self.assertTrue(xml_return_value, "count not generate xml for the article")
            generated_xml = read_file_content(TARGET_OUTPUT_DIR + expected_xml_file)
            model_xml = read_file_content(TEST_DATA_PATH + expected_xml_file)
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

    @patch('jatsgenerator.generate.write_xml_to_disk')
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
        """"
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
        self.assertFalse('other authors declare that no competing interests exist' in
                         article_xml.output_xml(pretty=True, indent='\t'))

    def test_set_copyright_authors(self):
        "start with an article then change the authors for test coverage for different input"
        article_id = 7
        article = generate.build_article_from_csv(article_id)
        # test the value as is with more than two authors
        article_xml = generate.build_xml(article_id, article)
        self.assertTrue(
            '<copyright-holder>Schuman et al</copyright-holder>' in article_xml.output_xml())
        # set authors to be exactly two
        for index, author in enumerate(article.contributors):
            if index > 1:
                del article.contributors[index]
        article_xml = generate.build_xml(article_id, article)
        self.assertTrue(
            '<copyright-holder>Schuman &amp; Barthel</copyright-holder>'
            in article_xml.output_xml())
        # set authors to be exactly one
        for index, author in enumerate(article.contributors):
            if index > 0:
                del article.contributors[index]
        article_xml = generate.build_xml(article_id, article)
        self.assertTrue(
            '<copyright-holder>Schuman</copyright-holder>' in article_xml.output_xml())
        # no authors
        article.contributors = []
        article_xml = generate.build_xml(article_id, article)
        self.assertTrue('<copyright-holder/>' in article_xml.output_xml())

    def test_set_copyright_license_date(self):
        "start with an article then remove the license date"
        article_id = 7
        article = generate.build_article_from_csv(article_id)
        # remove the license date
        if article.dates.get('license'):
            del article.dates['license']
        # change the accepted date just to be sure
        accepted_date = time.strptime("2037-11-13", "%Y-%m-%d")
        accepted_date_object = ArticleDate("pub", accepted_date)
        article.dates['accepted'] = accepted_date_object
        article_xml = generate.build_xml(article_id, article)
        self.assertTrue('<copyright-year>2037</copyright-year>' in article_xml.output_xml())

    def test_contributor_equal_contrib(self):
        "set equal_contrib on an author to test the output"
        article_id = 7
        article = generate.build_article_from_csv(article_id)
        # set all the authors as equal contributors
        for index, author in enumerate(article.contributors):
            if author.contrib_type == 'author':
                author.equal_contrib = True
        article_xml = generate.build_xml(article_id, article)
        self.assertTrue(
            '<contrib contrib-type="author" equal_contrib="yes" id="author-1399">'
            in article_xml.output_xml())
        self.assertTrue(
            '<contrib contrib-type="author" corresp="yes" equal_contrib="yes" id="author-1400">'
            in article_xml.output_xml())
        self.assertTrue(
            '<contrib contrib-type="author" corresp="yes" equal_contrib="yes" id="author-1013">'
            in article_xml.output_xml())

    def test_contributor_phone_fax(self):
        "set phone and fax on an author to test the output for test coverage"
        article_id = 7
        article = generate.build_article_from_csv(article_id)
        # set all the authors as equal contributors
        article.contributors[0].affiliations[0].phone = '555-5555'
        article.contributors[0].affiliations[0].fax = '555-5555'
        article_xml = generate.build_xml(article_id, article)
        self.assertTrue('<phone>555-5555</phone>' in article_xml.output_xml())
        self.assertTrue('<fax>555-5555</fax>' in article_xml.output_xml())

    def test_do_display_channel(self):
        "test when the display channel is blank"
        article_id = 7
        article = generate.build_article_from_csv(article_id)
        article.display_channel = None
        article_xml = generate.build_xml(article_id, article)
        self.assertTrue(
            '<subj-group subj-group-type="display-channel">' not in article_xml.output_xml())

    def test_do_subject_heading(self):
        "test when the article_categories is empty"
        article_id = 7
        article = generate.build_article_from_csv(article_id)
        article.article_categories = []
        article_xml = generate.build_xml(article_id, article)
        self.assertTrue(
            '<subj-group subj-group-type="heading">' not in article_xml.output_xml())

    def test_do_article_categories(self):
        "test when there is no display channel or article categories"
        article_id = 7
        article = generate.build_article_from_csv(article_id)
        article.display_channel = None
        article.article_categories = []
        article_xml = generate.build_xml(article_id, article)
        # now it should have no <article-categories> section at all
        self.assertTrue('<article-categories>' not in article_xml.output_xml())

    def test_author_keywords(self):
        "test setting author keywords which is currently disabled"
        article_id = 7
        article = generate.build_article_from_csv(article_id)
        article.display_channel = None
        article.article_categories = []
        article_xml = generate.build_xml(article_id, article)
        article_xml.set_kwd_group_author_keywords(article_xml.article_meta, article)
        self.assertTrue(
            '<kwd-group kwd-group-type="author-keywords">' in article_xml.output_xml())

if __name__ == '__main__':
    unittest.main()
