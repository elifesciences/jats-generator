import unittest
import time
from jatsgenerator import generate

class TestGenerate(unittest.TestCase):

    def setUp(self):
        pass

    def test_build_xml_from_csv(self):
        article_id = 7
        return_value = generate.build_xml_from_csv(article_id)
        self.assertTrue(return_value, "count not build article from csv")


if __name__ == '__main__':
    unittest.main()
