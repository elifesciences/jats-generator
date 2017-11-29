import unittest
import time
import os
from jatsgenerator import generate
from elifearticle.article import ArticleDate

TEST_BASE_PATH = os.path.dirname(os.path.abspath(__file__)) + os.sep
TEST_DATA_PATH = TEST_BASE_PATH + "test_data" + os.sep
TARGET_OUTPUT_DIR = TEST_BASE_PATH + "tmp" + os.sep
generate.settings.TARGET_OUTPUT_DIR = TARGET_OUTPUT_DIR

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

    def read_file_content(self, file_name):
        fp = open(file_name, 'rb')
        content = fp.read()
        fp.close()
        return content

    def test_build_xml_from_csv(self):
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
            xml_return_value = generate.build_xml(
                article_id, article, config_section, add_comment=False)
            self.assertTrue(xml_return_value, "count not generate xml for the article")
            generated_xml = self.read_file_content(TARGET_OUTPUT_DIR + expected_xml_file)
            model_xml = self.read_file_content(TEST_DATA_PATH + expected_xml_file)
            self.assertEqual(generated_xml, model_xml)


if __name__ == '__main__':
    unittest.main()
