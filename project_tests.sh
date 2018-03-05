#!/bin/bash
set -e

tox --recreate -e py35
. .tox/py35/bin/activate
pip install coveralls
COVERALLS_REPO_TOKEN=$(cat /etc/coveralls/tokens/jats-generator) coveralls
