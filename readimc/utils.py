"""Various utilities"""
import re

from typing import Optional
from xml.etree import ElementTree as ET

_XMLNS_REGEX = re.compile(r"{(?P<xmlns>.*)}")


def get_xmlns(elem: ET.Element) -> Optional[str]:
    """Get the XML namespace for a given element

    :param elem: the XML element
    :return: the namespace of the element
    """
    m = re.match(_XMLNS_REGEX, elem.tag)
    return m.group("xmlns") if m is not None else None
