import mmap
import numpy as np
import re
import xml.etree.ElementTree as ET

from imageio import imread
from os import PathLike
from typing import BinaryIO, List, Optional, Sequence, Union

from readimc._imc_file import IMCFile
from readimc._mcd_xml_parser import MCDXmlParser, MCDXmlParserError
from readimc.data import Slide, Panorama, Acquisition


class MCDFile(IMCFile):
    _METADATA_XMLNS_REGEX = re.compile(r"{(?P<xmlns>.*)}")

    def __init__(self, path: Union[str, PathLike]) -> None:
        """A class for reading IMC .mcd files

        :param path: path to the IMC .mcd file
        """
        super(MCDFile, self).__init__(path)
        self._fh: Optional[BinaryIO] = None
        self._metadata_xml: Optional[ET.Element] = None
        self._metadata_xmlns: Optional[str] = None
        self._slides: Optional[List[Slide]] = None

    @property
    def metadata_xml(self) -> ET.Element:
        """Full metadata in proprietary XML format"""
        if self._metadata_xml is None:
            raise IOError(f"MCD file '{self.path.name}' has not been opened")
        return self._metadata_xml

    @property
    def metadata_xmlns(self) -> str:
        """XML namespace of full metadata in proprietary XML format"""
        if self._metadata_xmlns is None:
            raise IOError(f"MCD file '{self.path.name}' has not been opened")
        return self._metadata_xmlns

    @property
    def metadata_xml_str(self) -> str:
        if self._metadata_xml is None or self._metadata_xmlns is None:
            raise IOError(f"MCD file '{self.path.name}' has not been opened")
        return ET.tostring(
            self._metadata_xml,
            encoding="unicode",
            xml_declaration=True,
            default_namespace=self._metadata_xmlns,
        )

    @property
    def slides(self) -> Sequence[Slide]:
        """Metadata on slides contained in this IMC .mcd file"""
        if self._slides is None:
            raise IOError(f"MCD file '{self.path.name}' has not been opened")
        return self._slides

    def __enter__(self) -> "MCDFile":
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def open(self) -> None:
        """Opens the IMC .mcd file for reading.

        It is good practice to use context managers whenever possible:

        .. code-block:: python

            with MCDFile("/path/to/file.mcd") as f:
                pass

        """
        if self._fh is not None:
            self._fh.close()
        self._fh = open(self._path, mode="rb")
        self._metadata_xml = self._read_metadata_xml()
        self._metadata_xmlns = self._get_metadata_xmlns(self.metadata_xml)
        try:
            self._slides = MCDXmlParser(
                self.metadata_xml, default_namespace=self.metadata_xmlns
            ).parse_slides()
        except MCDXmlParserError as e:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                "error parsing slide information from MCD-XML"
            ) from e

    def close(self) -> None:
        """Closes the IMC .mcd file.

        It is good practice to use context managers whenever possible:

        .. code-block:: python

            with MCDFile("/path/to/file.mcd") as f:
                pass

        """
        if self._fh is not None:
            self._fh.close()
            self._fh = None

    def read_acquisition(self, acquisition: Acquisition) -> np.ndarray:
        """Reads IMC acquisition data as numpy array.

        :param acquisition: the acquisition to read
        :return: the acquisition data as 32-bit floating point array,
            shape: (c, y, x)
        """
        if acquisition is None:
            raise ValueError("acquisition")
        try:
            data_start_offset = int(acquisition.metadata["DataStartOffset"])
            data_end_offset = int(acquisition.metadata["DataEndOffset"])
            value_bytes = int(acquisition.metadata["ValueBytes"])
        except (KeyError, ValueError) as e:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                "cannot locate acquisition image data"
            ) from e
        if data_start_offset >= data_end_offset:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                "invalid acquisition image data offsets"
            )
        if value_bytes <= 0:
            raise IOError("MCD file corrupted: invalid byte size")
        num_channels = acquisition.num_channels
        data_size = data_end_offset - data_start_offset
        bytes_per_pixel = (num_channels + 3) * value_bytes
        if data_size % bytes_per_pixel != 0:
            data_size += 1
        if data_size % bytes_per_pixel != 0:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                "invalid acquisition image data size"
            )
        num_pixels = data_size // bytes_per_pixel
        self._fh.seek(0)
        data = np.memmap(
            self._fh,
            dtype=np.float32,
            mode="r",
            offset=data_start_offset,
            shape=(num_pixels, num_channels + 3),
        )
        width, height = np.amax(data[:, :2], axis=0).astype(int) + 1
        if width * height != data.shape[0]:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                "inconsistent acquisition image data size"
            )
        img = np.zeros((height, width, num_channels), dtype=np.float32)
        img[data[:, 1].astype(int), data[:, 0].astype(int), :] = data[:, 3:]
        return np.moveaxis(img, -1, 0)

    def read_slide(self, slide: Slide) -> Optional[np.ndarray]:
        """Reads and decodes a slide image as numpy array using the ``imageio``
        package.

        .. note::
            Slide images are stored as binary data within the IMC .mcd file in
            an arbitrary encoding. The ``imageio`` package can decode most
            commonly used image file formats, but may fail for more obscure,
            in which case an ``IOException`` is raised.

        :param slide: the slide to read
        :return: the slide image, or ``None`` if no image is available for the
            specified slide
        """
        try:
            data_start_offset = int(slide.metadata["ImageStartOffset"])
            data_end_offset = int(slide.metadata["ImageEndOffset"])
        except (KeyError, ValueError) as e:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                f"cannot locate image data for slide {slide.id}"
            ) from e
        if data_start_offset == data_end_offset == 0:
            return None
        data_start_offset += 161
        if data_start_offset >= data_end_offset:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                f"invalid image data offsets for slide {slide.id}"
            )
        try:
            return self._read_image(
                data_start_offset, data_end_offset - data_start_offset
            )
        except Exception as e:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                f"cannot read image for slide {slide.id}"
            ) from e

    def read_panorama(self, panorama: Panorama) -> np.ndarray:
        """Reads and decodes a panorama image as numpy array using the
        ``imageio`` package.

        :param panorama: the panorama to read
        :return: the panorama image as numpy array
        """
        try:
            data_start_offset = int(panorama.metadata["ImageStartOffset"])
            data_end_offset = int(panorama.metadata["ImageEndOffset"])
        except (KeyError, ValueError) as e:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                f"cannot locate image data for panorama {panorama.id}"
            ) from e
        data_start_offset += 161
        if data_start_offset >= data_end_offset:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                f"invalid image data offsets for panorama {panorama.id}"
            )
        try:
            return self._read_image(
                data_start_offset, data_end_offset - data_start_offset
            )
        except Exception as e:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                f"cannot read image for panorama {panorama.id}"
            ) from e

    def read_before_ablation_image(
        self, acquisition: Acquisition
    ) -> Optional[np.ndarray]:
        """Reads and decodes a before-ablation image as numpy array using the
        ``imageio`` package.

        :param acquisition: the acquisition for which to read the
            before-ablation image
        :return: the before-ablation image as numpy array, or ``None`` if no
            before-ablation image is available for the specified acquisition
        """
        try:
            data_start_offset = int(
                acquisition.metadata["BeforeAblationImageStartOffset"]
            )
            data_end_offset = int(
                acquisition.metadata["BeforeAblationImageEndOffset"]
            )
        except (KeyError, ValueError) as e:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                f"cannot locate before-ablation image data "
                f"for acquisition {acquisition.id}"
            ) from e
        if data_start_offset == data_end_offset == 0:
            return None
        data_start_offset += 161
        if data_start_offset >= data_end_offset:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                f"invalid before-ablation image data offsets "
                f"for acquisition {acquisition.id}"
            )
        try:
            return self._read_image(
                data_start_offset, data_end_offset - data_start_offset
            )
        except Exception as e:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                f"cannot read before-ablation image "
                f"for acquisition {acquisition.id}"
            ) from e

    def read_after_ablation_image(
        self, acquisition: Acquisition
    ) -> Optional[np.ndarray]:
        """Reads and decodes a after-ablation image as numpy array using the
        ``imageio`` package.

        :param acquisition: the acquisition for which to read the
            after-ablation image
        :return: the after-ablation image as numpy array, or ``None`` if no
            after-ablation image is available for the specified acquisition
        """
        try:
            data_start_offset = int(
                acquisition.metadata["AfterAblationImageStartOffset"]
            )
            data_end_offset = int(
                acquisition.metadata["AfterAblationImageEndOffset"]
            )
        except (KeyError, ValueError) as e:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                f"cannot locate after-ablation image data "
                f"for acquisition {acquisition.id}"
            ) from e
        if data_start_offset == data_end_offset == 0:
            return None
        data_start_offset += 161
        if data_start_offset >= data_end_offset:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                f"invalid after-ablation image data offsets "
                f"for acquisition {acquisition.id}"
            )
        try:
            return self._read_image(
                data_start_offset, data_end_offset - data_start_offset
            )
        except Exception as e:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                f"cannot read after-ablation image "
                f"for acquisition {acquisition.id}"
            ) from e

    def _read_metadata_xml(
        self,
        encoding: str = "utf-16-le",
        start_sub: str = "<MCDSchema",
        end_sub: str = "</MCDSchema>",
    ) -> ET.Element:
        with mmap.mmap(self._fh.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            # V1 contains multiple MCDSchema entries
            # As per imctools, the latest entry should be taken
            start_sub_encoded = start_sub.encode(encoding=encoding)
            start_index = mm.rfind(start_sub_encoded)
            if start_index == -1:
                raise IOError(
                    f"MCD file '{self.path.name}' corrupted: "
                    f"start of XML document '{start_sub}' not found"
                )
            end_sub_encoded = end_sub.encode(encoding=encoding)
            end_index = mm.rfind(end_sub_encoded, start_index)
            if end_index == -1:
                raise IOError(
                    f"MCD file '{self.path.name}' corrupted: "
                    f"end of XML document '{end_sub}' not found"
                )
            mm.seek(start_index)
            data = mm.read(end_index + len(end_sub_encoded) - start_index)
        text = data.decode(encoding=encoding)
        return ET.fromstring(text)

    def _read_image(self, data_offset: int, data_size: int) -> np.ndarray:
        self._fh.seek(data_offset)
        data = self._fh.read(data_size)
        return imread(data)

    @staticmethod
    def _get_metadata_xmlns(elem: ET.Element) -> str:
        m = re.match(MCDFile._METADATA_XMLNS_REGEX, elem.tag)
        return m.group("xmlns") if m is not None else ""

    def __repr__(self) -> str:
        return str(self._path)
