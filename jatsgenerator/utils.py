"""Utility functions for generating JATS"""

import re
from xml.dom import minidom
from elifetools import utils as etoolsutils
from elifetools import xmlio


def tag_wrap(tag_name, content):
    """wrap the content with a tag of tag_name"""
    return "<{tag}>{content}</{tag}>".format(tag=tag_name, content=content)


def append_to_tag(parent, tag_name, string):
    "method to retain inline tagging when adding to a parent tag"
    # Escape any unescaped ampersands and apostrophes
    escaped_string = etoolsutils.escape_ampersand(string)
    tagged_string = tag_wrap(tag_name, escaped_string)
    # XML
    reparsed = minidom.parseString(tagged_string.encode("utf8"))
    root_xml_element = xmlio.append_minidom_xml_to_elementtree_xml(parent, reparsed)
    return root_xml_element


def object_id_from_uri(uri):
    """
    from a sciety.org uri extract the DOI portion to be an id value
    e.g. from https://sciety.org/articles/activity/10.1101/865006
    return 10.1101/865006
    """
    if uri:
        id_match_pattern = re.compile(r".*?/(10\..*)")
        matches = id_match_pattern.match(uri)
        if matches:
            return matches.group(1)
        return uri
    return uri
