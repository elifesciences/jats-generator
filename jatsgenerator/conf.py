import configparser
import json

CONFIG_FILE = "jatsgenerator.cfg"
BOOLEAN_VALUES = []
INT_VALUES = []
LIST_VALUES = ["journal_id_types", "contrib_types", "history_date_types"]


def load_config(config_file=CONFIG_FILE):
    config = configparser.ConfigParser(interpolation=None)
    config.read(config_file)
    return config


def raw_config(config_section, config_file=CONFIG_FILE):
    "try to load the config section"
    config = load_config(config_file)
    if config.has_section(config_section):
        return config[config_section]
    # default
    return config.defaults()


def boolean_config(config, value_name):
    "extract the value as a boolean"
    return config.getboolean(value_name)


def int_config(config, value_name):
    "extract the value as an int"
    return config.getint(value_name)


def list_config(config, value_name):
    "extract the value as a list parsed from JSON"
    return json.loads(config.get(value_name))


def parse_raw_config(config):
    "parse the raw config to something good"
    config_dict = {}

    for value_name in config:
        if value_name in BOOLEAN_VALUES:
            config_dict[value_name] = boolean_config(config, value_name)
        elif value_name in INT_VALUES:
            config_dict[value_name] = int_config(config, value_name)
        elif value_name in LIST_VALUES:
            config_dict[value_name] = list_config(config, value_name)
        else:
            # default
            config_dict[value_name] = config.get(value_name)
    return config_dict
