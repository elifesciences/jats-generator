import unittest
from jatsgenerator import conf

class TestConf(unittest.TestCase):

    def test_load_config(self):
        "test loading when no config file is specified for test coverage"
        self.assertIsNotNone(conf.load_config(None))


if __name__ == '__main__':
    unittest.main()
