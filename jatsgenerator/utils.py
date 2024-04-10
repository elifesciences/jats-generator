"""Utility functions for generating JATS"""

import re
from elifetools import utils as etoolsutils
from elifetools import xmlio


# namespaces for when reparsing XML strings
XML_NAMESPACE_MAP = {
    "ali": "http://www.niso.org/schemas/ali/1.0/",
    "mml": "http://www.w3.org/1998/Math/MathML",
    "xlink": "http://www.w3.org/1999/xlink",
}


def reparsing_namespaces(namespace_map):
    """compile a string representation of the namespaces"""
    namespace_string = ""
    for prefix, uri in namespace_map.items():
        namespace_string += 'xmlns:%s="%s" ' % (prefix, uri)
    return namespace_string.rstrip()


def allowed_tags():
    "tuple of whitelisted tags"
    return (
        "<p>",
        "<p ",
        "</p>",
        "<disp-quote",
        "</disp-quote>",
        "<italic>",
        "</italic>",
        "<bold>",
        "</bold>",
        "<underline>",
        "</underline>",
        "<sub>",
        "</sub>",
        "<sup>",
        "</sup>",
        "<sc>",
        "</sc>",
        "<inline-formula>",
        "</inline-formula>",
        "<disp-formula>",
        "</disp-formula>",
        "<mml:",
        "</mml:",
        "<ext-link",
        "</ext-link>",
        "<list>",
        "<list ",
        "</list>",
        "<list-item",
        "</list-item>",
        "<label>",
        "</label>",
        "<title>",
        "</title>",
        "<caption>",
        "</caption>",
        "<graphic ",
        "</graphic>",
        "<table",
        "<table ",
        "</table>",
        "<thead>",
        "</thead>",
        "<tbody>",
        "</tbody>",
        "<tr>",
        "</tr>",
        "<th>",
        "<th",
        "</th>",
        "<td>",
        "<td ",
        "</td>",
        "<xref ",
        "</xref>",
        "<break",
        "<fig",
        "</fig>"
    )


def append_to_tag(
    parent,
    tag_name,
    original_string,
    namespace_map=None,
    attributes=None,
    attributes_text="",
):
    """
    method to retain inline tagging when adding to a parent tag
    escape and reparse the string then add it to the parent tag
    """
    tag_converted_string = etoolsutils.escape_ampersand(original_string)
    tag_converted_string = etoolsutils.escape_unmatched_angle_brackets(
        tag_converted_string, allowed_tags()
    )
    namespaces_string = ""
    if namespace_map:
        namespaces_string = reparsing_namespaces(namespace_map)
    minidom_tag = xmlio.reparsed_tag(
        tag_name, tag_converted_string, namespaces_string, attributes_text
    )
    root_xml_element = xmlio.append_minidom_xml_to_elementtree_xml(
        parent, minidom_tag, attributes=attributes, child_attributes=True
    )
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
