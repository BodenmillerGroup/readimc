from typing import Dict, List, Optional
from xml.etree import ElementTree as ET

import readimc.data


class IMCMCDXMLParserError(Exception):
    pass


class IMCMCDXMLParser:
    def __init__(
        self,
        mcd_schema_elem: ET.Element,
        default_namespace: Optional[str] = None,
    ) -> None:
        self._mcd_schema_elem = mcd_schema_elem
        self._default_namespace = default_namespace

    def parse_slides(self) -> List[readimc.data.Slide]:
        slides = [
            self._parse_slide(slide_elem)
            for slide_elem in self._find_elements("Slide")
        ]
        slides.sort(key=lambda slide: slide.id)
        return slides

    def _parse_slide(self, slide_elem: ET.Element) -> readimc.data.Slide:
        slide_panoramas: List[readimc.data.Panorama] = []
        slide_acquisitions: List[readimc.data.Acquisition] = []
        slide = readimc.data.Slide(
            self._get_text_as_int(slide_elem, "ID"),
            self._get_metadata_dict(slide_elem),
            slide_panoramas,
            slide_acquisitions,
        )
        panorama_elems = self._find_elements(f"Panorama[SlideID='{slide.id}']")
        for panorama_elem in panorama_elems:
            panorama_id = self._get_text_as_int(panorama_elem, "ID")
            panorama_type = self._get_text_or_none(panorama_elem, "Type")
            if panorama_type != "Default":  # ignore "virtual" Panoramas
                panorama = self._parse_panorama(panorama_elem, slide)
                slide_panoramas.append(panorama)
            acquisition_roi_elems = self._find_elements(
                f"AcquisitionROI[PanoramaID='{panorama_id}']"
            )
            for acquisition_roi_elem in acquisition_roi_elems:
                acquisition_roi_id = self._get_text_as_int(
                    acquisition_roi_elem, "ID"
                )
                acquisition_elems = self._find_elements(
                    f"Acquisition[AcquisitionROIID='{acquisition_roi_id}']"
                )
                for acquisition_elem in acquisition_elems:
                    acquisition = self._parse_acquisition(
                        acquisition_elem, slide
                    )
                    slide_acquisitions.append(acquisition)
        slide_panoramas.sort(key=lambda panorama: panorama.id)
        slide_acquisitions.sort(key=lambda acquisition: acquisition.id)
        return slide

    def _parse_panorama(
        self, panorama_elem: ET.Element, slide: readimc.data.Slide
    ) -> readimc.data.Panorama:
        return readimc.data.Panorama(
            slide,
            self._get_text_as_int(panorama_elem, "ID"),
            self._get_metadata_dict(panorama_elem),
        )

    def _parse_acquisition(
        self, acquisition_elem: ET.Element, slide: readimc.data.Slide
    ) -> readimc.data.Acquisition:
        acquisition_channel_names: List[str] = []
        acquisition_channel_labels: List[str] = []
        acquisition = readimc.data.Acquisition(
            slide,
            self._get_text_as_int(acquisition_elem, "ID"),
            self._get_metadata_dict(acquisition_elem),
            acquisition_channel_names,
            acquisition_channel_labels,
        )
        acquisition_channel_elems = self._find_elements(
            f"AcquisitionChannel[AcquisitionID='{acquisition.id}']"
        )
        acquisition_channel_elems.sort(
            key=lambda acquisition_channel_elem: self._get_text_as_int(
                acquisition_channel_elem, "OrderNumber"
            )
        )
        for acquisition_channel_elem in acquisition_channel_elems:
            channel_name = self._get_text(
                acquisition_channel_elem, "ChannelName"
            )
            channel_label = self._get_text(
                acquisition_channel_elem, "ChannelLabel"
            )
            acquisition_channel_names.append(channel_name)
            acquisition_channel_labels.append(channel_label)
        if tuple(acquisition_channel_names[:3]) != ("X", "Y", "Z"):
            raise IMCMCDXMLParserError(
                f"XYZ channels not found for acquisition {acquisition.id}"
            )
        del acquisition_channel_names[:3]
        del acquisition_channel_labels[:3]
        return acquisition

    def _find_elements(self, path: str) -> List[ET.Element]:
        namespaces = None
        if self._default_namespace is not None:
            namespaces = {"": self._default_namespace}
        return self._mcd_schema_elem.findall(path, namespaces=namespaces)

    def _get_text_or_none(
        self, parent_elem: ET.Element, tag: str
    ) -> Optional[str]:
        namespaces = None
        if self._default_namespace is not None:
            namespaces = {"": self._default_namespace}
        elem = parent_elem.find(tag, namespaces=namespaces)
        return (elem.text or "") if elem is not None else None

    def _get_text(self, parent_elem: ET.Element, tag: str) -> str:
        text = self._get_text_or_none(parent_elem, tag)
        if text is None:
            raise IMCMCDXMLParserError(
                f"XML tag '{tag}' not found "
                f"for parent XML tag '{parent_elem.tag}'"
            )
        return text

    def _get_text_as_int(self, parent_elem: ET.Element, tag: str) -> int:
        text = self._get_text(parent_elem, tag)
        try:
            return int(text)
        except ValueError as e:
            raise IMCMCDXMLParserError(
                f"Text '{text}' of XML tag '{tag}' cannot be converted to int "
                f"for parent XML tag '{parent_elem.tag}'"
            ) from e

    def _get_metadata_dict(self, parent_elem: ET.Element) -> Dict[str, str]:
        metadata = {}
        for elem in parent_elem:
            tag = elem.tag.replace(f"{{{self._default_namespace}}}", "")
            metadata[tag] = elem.text or ""
        return metadata
