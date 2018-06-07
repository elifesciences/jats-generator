import configparser as configparser
import json

CONFIG_FILE = 'jatsgenerator.cfg'

def load_config(config_file=None):
    if not config_file:
        config_file=CONFIG_FILE
    config = configparser.ConfigParser(interpolation=None)
    config.read(config_file)
    return config

def raw_config(config_section, config_file=None):
    "try to load the config section"
    if not config_file:
        config_file=CONFIG_FILE
    config = load_config(config_file)
    if config.has_section(config_section):
        return config[config_section]
    # default
    return config['DEFAULT']

def parse_raw_config(raw_config):
    "parse the raw config to something good"
    jats_config = {}
    boolean_values = []
    int_values = []
    list_values = []

    list_values.append("journal_id_types")
    list_values.append("contrib_types")
    list_values.append("history_date_types")

    for value_name in raw_config:
        if value_name in boolean_values:
            jats_config[value_name] = raw_config.getboolean(value_name)
        elif value_name in int_values:
            jats_config[value_name] = raw_config.getint(value_name)
        elif value_name in list_values:
            jats_config[value_name] = json.loads(raw_config.get(value_name))
        else:
            # default
            jats_config[value_name] = raw_config.get(value_name)
    return jats_config
