import re

from typing import Optional
from xml.etree import ElementTree as ET

_XMLNS_REGEX = re.compile(r"{(?P<xmlns>.*)}")


def get_xmlns(elem: ET.Element) -> Optional[str]:
    m = re.match(_XMLNS_REGEX, elem.tag)
    return m.group("xmlns") if m is not None else None
