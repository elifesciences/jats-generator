import unittest
import configparser as configparser
from jatsgenerator import conf


def build_config_for_testing(value_name, value):
    "build a config object with one value and return the defaults for testing"
    config = configparser.ConfigParser(interpolation=None)
    config['DEFAULT'][value_name] = value
    new_config = config['DEFAULT']
    return new_config


class TestConf(unittest.TestCase):

    def setUp(self):
        # some values for testing
        self.boolean_value = 'True'
        self.boolean_expected = True
        self.int_value = '42'
        self.int_expected = 42
        self.list_value = '[1,1,2,3,5]'
        self.list_expected = [1,1,2,3,5]
        # save conf values prior to testing
        self.old_boolean_values = conf.BOOLEAN_VALUES
        self.old_int_values = conf.INT_VALUES
        self.old_list_values = conf.LIST_VALUES

    def tearDown(self):
        # reset the conf values
        conf.BOOLEAN_VALUES = self.old_boolean_values
        conf.INT_VALUES = self.old_int_values
        conf.LIST_VALUES = self.old_list_values

    def test_load_config(self):
        "test loading when no config file is specified for test coverage"
        self.assertIsNotNone(conf.load_config())


    def test_boolean_config(self):
        "test parsing a boolean value"
        value = self.boolean_value
        value_name = 'test'
        expected = self.boolean_expected
        config = build_config_for_testing(value_name, value)
        self.assertEqual(conf.boolean_config(config, value_name), expected)


    def test_int_config(self):
        "test parsing an int value"
        value = self.int_value
        value_name = 'test'
        expected = self.int_expected
        config = build_config_for_testing(value_name, value)
        self.assertEqual(conf.int_config(config, value_name), expected)


    def test_list_config(self):
        "test parsing a list value"
        value = self.list_value
        value_name = 'test'
        expected = self.list_expected
        config = build_config_for_testing(value_name, value)
        self.assertEqual(conf.list_config(config, value_name), expected)


    def test_parse_raw_config(self):
        "test parsing a raw config of all the different value types"
        # override the library values
        conf.BOOLEAN_VALUES = ['test_boolean']
        conf.INT_VALUES = ['test_int']
        conf.LIST_VALUES = ['test_list']
        # build a config object
        config = configparser.ConfigParser(interpolation=None)
        config['DEFAULT']['test_boolean'] = self.boolean_value
        config['DEFAULT']['test_int'] = self.int_value
        config['DEFAULT']['test_list'] = self.list_value
        # parse the raw config for coverage
        config_dict = conf.parse_raw_config(config['DEFAULT'])
        # assert some things
        self.assertIsNotNone(config_dict)
        self.assertEqual(config_dict.get('test_boolean'), self.boolean_expected)
        self.assertEqual(config_dict.get('test_int'), self.int_expected)
        self.assertEqual(config_dict.get('test_list'), self.list_expected)


if __name__ == '__main__':
    unittest.main()
