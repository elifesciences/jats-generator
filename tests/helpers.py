import os
from jatsgenerator.conf import raw_config, parse_raw_config

TEST_BASE_PATH = os.path.dirname(os.path.abspath(__file__)) + os.sep
TEST_DATA_PATH = TEST_BASE_PATH + "test_data" + os.sep
TARGET_OUTPUT_DIR = TEST_BASE_PATH + "tmp" + os.sep


def build_config(config_section):
    "build the config and override the output directory"
    jats_config = parse_raw_config(raw_config(config_section))
    jats_config["target_output_dir"] = TARGET_OUTPUT_DIR
    return jats_config


def read_file_content(file_name):
    with open(file_name, "rb") as open_file:
        content = open_file.read()
    return content
