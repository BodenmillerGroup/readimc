import itertools
import re
from typing import Dict, List, Optional, Tuple
from warnings import warn
from xml.etree import ElementTree as ET

from .data import Acquisition, Panorama, Slide


class MCDParserError(Exception):
    def __init__(self, *args) -> None:
        """Error occurring when parsing invalid IMC .mcd file metadata"""
        super(MCDParserError, self).__init__(*args)


class MCDParser:
    _XMLNS_REGEX = re.compile(r"{(?P<xmlns>.*)}")
    _CHANNEL_REGEX = re.compile(r"^(?P<metal>[a-zA-Z]+)\((?P<mass>[0-9]+)\)$")

    def __init__(self, schema_xml: str) -> None:
        """A class for parsing IMC .mcd file metadata

        :param schema_xml: IMC .mcd file metadata in proprietary XML format
        """
        self._schema_xml = schema_xml
        self._schema_xml_elem = ET.fromstring(self._schema_xml)
        m = self._XMLNS_REGEX.match(self._schema_xml_elem.tag)
        self._schema_xml_xmlns = m.group("xmlns") if m is not None else None

    @property
    def schema_xml(self) -> str:
        """Full IMC .mcd file metadata in proprietary XML format"""
        return self._schema_xml

    @property
    def schema_xml_elem(self) -> ET.Element:
        """Full IMC .mcd file metadata as Python ElementTree element"""
        return self._schema_xml_elem

    @property
    def schema_xml_xmlns(self) -> Optional[str]:
        """Value of the metadata `xmlns` XML namespace attribute"""
        return self._schema_xml_xmlns

    @property
    def metadata(self) -> str:
        """Legacy accessor for `schema_xml`"""
        warn(
            "`MCDParser.metadata` will be removed in future readimc releases; "
            "use `MCDFile.schema_xml` instead"
        )
        return self.schema_xml

    @property
    def metadata_elem(self) -> ET.Element:
        """Legacy accessor for `schema_xml_elem`"""
        warn(
            "`MCDParser.metadata_elem` will be removed in future readimc releases; "
            "use `MCDFile.schema_xml_elem` instead"
        )
        return self.schema_xml_elem

    @property
    def metadata_xmlns(self) -> Optional[str]:
        """Legacy accessor for `schema_xml_xmlns`"""
        warn(
            "`MCDParser.metadata_xmlns` will be removed in future readimc releases; "
            "use `MCDFile.schema_xml_xmlns` instead"
        )
        return self.schema_xml_xmlns

    def parse_slides(self) -> List[Slide]:
        """Extract slide metadata"""
        slides = [
            self._parse_slide(slide_elem) for slide_elem in self._find_elements("Slide")
        ]
        slides.sort(key=lambda slide: slide.id)
        return slides

    def _parse_slide(self, slide_elem: ET.Element) -> Slide:
        slide = Slide(
            self._get_text_as_int(slide_elem, "ID"),
            self._get_metadata_dict(slide_elem),
        )
        panorama_elems = self._find_elements(f"Panorama[SlideID='{slide.id}']")
        for panorama_elem in panorama_elems:
            panorama = None
            panorama_id = self._get_text_as_int(panorama_elem, "ID")
            panorama_type = self._get_text_or_none(panorama_elem, "Type")
            if panorama_type != "Default":  # ignore "virtual" Panoramas
                panorama = self._parse_panorama(panorama_elem, slide)
                slide.panoramas.append(panorama)
            acquisition_roi_elems = self._find_elements(
                f"AcquisitionROI[PanoramaID='{panorama_id}']"
            )
            for acquisition_roi_elem in acquisition_roi_elems:
                acquisition_roi_id = self._get_text_as_int(acquisition_roi_elem, "ID")
                roi_point_elems = self._find_elements(
                    f"ROIPoint[AcquisitionROIID='{acquisition_roi_id}']"
                )
                roi_points_um = None
                if len(roi_point_elems) == 4:
                    roi_points_um = tuple(
                        (
                            self._get_text_as_float(roi_point_elem, "SlideXPosUm"),
                            self._get_text_as_float(roi_point_elem, "SlideYPosUm"),
                        )
                        for roi_point_elem in sorted(
                            roi_point_elems,
                            key=lambda roi_point_elem: self._get_text_as_int(
                                roi_point_elem, "OrderNumber"
                            ),
                        )
                    )
                acquisition_elems = self._find_elements(
                    f"Acquisition[AcquisitionROIID='{acquisition_roi_id}']"
                )
                for acquisition_elem in acquisition_elems:
                    acquisition = self._parse_acquisition(
                        acquisition_elem, slide, panorama, roi_points_um  # type: ignore
                    )
                    slide.acquisitions.append(acquisition)
                    if panorama is not None:
                        panorama.acquisitions.append(acquisition)
        for a, b in itertools.combinations(slide.acquisitions, 2):
            a_start = a.metadata["DataStartOffset"]
            a_end = a.metadata["DataEndOffset"]
            b_start = b.metadata["DataStartOffset"]
            b_end = b.metadata["DataEndOffset"]
            if b_start <= a_start < b_end or b_start < a_end <= b_end:
                warn(
                    f"Slide {slide.id} corrupted: "
                    f"overlapping memory blocks for acquisitions {a.id} and {b.id}"
                )
        slide.panoramas.sort(key=lambda panorama: panorama.id)
        slide.acquisitions.sort(key=lambda acquisition: acquisition.id)
        return slide

    def _parse_panorama(self, panorama_elem: ET.Element, slide: Slide) -> Panorama:
        return Panorama(
            slide,
            self._get_text_as_int(panorama_elem, "ID"),
            self._get_metadata_dict(panorama_elem),
        )

    def _parse_acquisition(
        self,
        acquisition_elem: ET.Element,
        slide: Slide,
        panorama: Optional[Panorama],
        roi_points_um: Optional[
            Tuple[
                Tuple[float, float],
                Tuple[float, float],
                Tuple[float, float],
                Tuple[float, float],
            ]
        ],
    ) -> Acquisition:
        acquisition_id = self._get_text_as_int(acquisition_elem, "ID")
        acquisition_channel_elems = self._find_elements(
            f"AcquisitionChannel[AcquisitionID='{acquisition_id}']"
        )
        acquisition_channel_elems.sort(
            key=lambda acquisition_channel_elem: self._get_text_as_int(
                acquisition_channel_elem, "OrderNumber"
            )
        )
        acquisition = Acquisition(
            slide,
            panorama,
            acquisition_id,
            roi_points_um,
            self._get_metadata_dict(acquisition_elem),
            len(acquisition_channel_elems) - 3,
        )
        for i, acquisition_channel_elem in enumerate(acquisition_channel_elems):
            channel_name = self._get_text(acquisition_channel_elem, "ChannelName")
            if i == 0 and channel_name != "X":
                raise MCDParserError(
                    f"First channel '{channel_name}' should be named 'X'"
                )
            if i == 1 and channel_name != "Y":
                raise MCDParserError(
                    f"Second channel '{channel_name}' should be named 'Y'"
                )
            if i == 2 and channel_name != "Z":
                raise MCDParserError(
                    f"Third channel '{channel_name}' should be named 'Z'"
                )
            if channel_name in ("X", "Y", "Z"):
                continue
            m = self._CHANNEL_REGEX.match(channel_name)
            if m is None:
                raise MCDParserError(
                    "Cannot extract channel information "
                    f"from channel name '{channel_name}' "
                    f"for acquisition {acquisition.id}"
                )
            channel_label = self._get_text(acquisition_channel_elem, "ChannelLabel")
            acquisition._channel_metals.append(m.group("metal"))
            acquisition._channel_masses.append(int(m.group("mass")))
            acquisition._channel_labels.append(channel_label)
        return acquisition

    def _find_elements(self, path: str) -> List[ET.Element]:
        namespaces = None
        if self._schema_xml_xmlns is not None:
            namespaces = {"": self._schema_xml_xmlns}
        return self._schema_xml_elem.findall(path, namespaces=namespaces)

    def _get_text_or_none(self, parent_elem: ET.Element, tag: str) -> Optional[str]:
        namespaces = None
        if self._schema_xml_xmlns is not None:
            namespaces = {"": self._schema_xml_xmlns}
        elem = parent_elem.find(tag, namespaces=namespaces)
        return (elem.text or "") if elem is not None else None

    def _get_text(self, parent_elem: ET.Element, tag: str) -> str:
        text = self._get_text_or_none(parent_elem, tag)
        if text is None:
            raise MCDParserError(
                f"XML tag '{tag}' not found for parent XML tag '{parent_elem.tag}'"
            )
        return text

    def _get_text_as_int(self, parent_elem: ET.Element, tag: str) -> int:
        text = self._get_text(parent_elem, tag)
        try:
            return int(text)
        except ValueError as e:
            raise MCDParserError(
                f"Text '{text}' of XML tag '{tag}' cannot be converted to int "
                f"for parent XML tag '{parent_elem.tag}'"
            ) from e

    def _get_text_as_float(self, parent_elem: ET.Element, tag: str) -> float:
        text = self._get_text(parent_elem, tag)
        try:
            return float(text)
        except ValueError as e:
            raise MCDParserError(
                f"Text '{text}' of XML tag '{tag}' cannot be converted to "
                f"float for parent XML tag '{parent_elem.tag}'"
            ) from e

    def _get_metadata_dict(self, parent_elem: ET.Element) -> Dict[str, str]:
        metadata = {}
        for elem in parent_elem:
            tag = elem.tag
            if self._schema_xml_xmlns is not None:
                tag = tag.replace(f"{{{self._schema_xml_xmlns}}}", "")
            metadata[tag] = elem.text or ""
        return metadata
