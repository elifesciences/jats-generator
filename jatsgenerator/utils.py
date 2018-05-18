"""Utility functions for generating JATS"""

def tag_wrap(tag_name, content):
    """wrap the content with a tag of tag_name"""
    return u'<{tag}>{content}</{tag}>'.format(tag=tag_name, content=content)
