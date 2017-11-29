import configparser as configparser
import json

config = configparser.ConfigParser(interpolation=None)
config.read('jatsgenerator.cfg')

def parse_raw_config(raw_config):
    "parse the raw config to something good"
    jats_config = {}
    boolean_values = []
    int_values = []
    list_values = []

    list_values.append("journal_id_types")

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
