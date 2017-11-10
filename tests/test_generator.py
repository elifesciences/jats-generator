import unittest
import time
from jatsgenerator import generate

class TestGenerate(unittest.TestCase):

    def setUp(self):
        pass

    def test_dummy(self):
        self.assertEqual(generate.dummy(), None)


if __name__ == '__main__':
    unittest.main()
