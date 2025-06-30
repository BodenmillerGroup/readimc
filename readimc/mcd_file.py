import mmap
import tempfile
from os import W_OK, PathLike, access, path
from pathlib import Path
from typing import BinaryIO, List, Optional, Sequence, Tuple, Union
from warnings import warn

import numpy as np
from imageio.v2 import imread

from .data import Acquisition, Panorama, Slide
from .imc_file import IMCFile
from .mcd_parser import MCDParser, MCDParserError


class MCDFile(IMCFile):
    def __init__(self, path: Union[str, PathLike]) -> None:
        """A class for reading IMC .mcd files

        :param path: path to the IMC .mcd file
        """
        super(MCDFile, self).__init__(path)
        self._fh: Optional[BinaryIO] = None
        self._schema_xml: Optional[str] = None
        self._slides: Optional[List[Slide]] = None

    @property
    def schema_xml(self) -> str:
        """Full metadata in proprietary XML format"""
        if self._schema_xml is None:
            raise IOError(f"MCD file '{self.path.name}' has not been opened")
        return self._schema_xml

    @property
    def metadata(self) -> str:
        """Legacy accessor for `schema_xml`"""
        warn(
            "`MCDFile.metadata` will be removed in future readimc releases; "
            "use `MCDFile.schema_xml` instead"
        )
        return self.schema_xml

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
        self._schema_xml = self._read_schema_xml()
        try:
            self._slides = MCDParser(self._schema_xml).parse_slides()
        except MCDParserError as e:
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

    def read_acquisition(
        self,
        acquisition: Optional[Acquisition] = None,
        strict: bool = True,
        channels: Optional[List[int]] = None,
        region: Optional[Tuple[int, int, int, int]] = None,
        create_temp_file: Optional[Path] = None,
    ) -> np.ndarray:
        """Reads IMC acquisition data as a numpy array with optional
        memory-mapping and/or subsetting.

        :param acquisition: The acquisition to read.
        :param strict: If True, raises errors for inconsistencies; otherwise,
        warns and recovers.
        :param channels: List of channel indices to load (zero-based).
        :param region: Tuple (x_min, y_min, x_max, y_max) to subset the image region.
        :param create_temp_file: Directory to store a temporary file (if provided,
        memory-mapping is used).
        :return: The acquisition data as a 32-bit float array, shape (c, y, x).
        """
        if acquisition is None:
            raise ValueError("acquisition must be specified")
        if self._fh is None:
            raise IOError(f"MCD file '{self.path.name}' has not been opened")
        if region is not None and not all(isinstance(c, int) for c in region):
            raise ValueError("region must be a tuple of integers")
        if region is not None:
            if region[0] >= region[2] or region[1] >= region[3]:
                raise ValueError("region must be (x_min, y_min, x_max, y_max)")

        # Handle the create_temp_file directory argument.
        if create_temp_file:
            if not isinstance(create_temp_file, (str, Path)):
                raise ValueError("create_temp_file must be a string or Path object.")
            create_temp_file = Path(create_temp_file)
            if not create_temp_file.exists() or not access(str(create_temp_file), W_OK):
                raise PermissionError(f"The path {create_temp_file} is not writable.")

        # Read necessary metadata from acquisition
        try:
            data_start_offset = int(acquisition.metadata["DataStartOffset"])
            data_end_offset = int(acquisition.metadata["DataEndOffset"])
            value_bytes = int(acquisition.metadata["ValueBytes"])
            width = int(acquisition.metadata["MaxX"])
            height = int(acquisition.metadata["MaxY"])
        except (KeyError, ValueError) as e:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: missing metadata"
            ) from e

        # Get the file size to check offset validity
        file_size = path.getsize(self.path)
        if data_start_offset > data_end_offset or value_bytes <= 0:
            raise IOError("MCD file corrupted: invalid data offsets or byte size")
        if data_start_offset == data_end_offset:
            warn(f"MCD file '{self.path.name}' contains empty acquisition image data")
        if data_end_offset > file_size:
            raise IOError(
                f"MCD file corrupted: data_end_offset ({data_end_offset}) "
                f"exceeds file size ({file_size})."
            )

        # Compute bytes per pixel and validate data size
        num_channels = acquisition.num_channels
        bytes_per_pixel = (num_channels + 3) * value_bytes
        data_size = data_end_offset - data_start_offset
        if data_size % bytes_per_pixel != 0:
            if strict:
                raise IOError(
                    f"MCD file '{self.path.name}' corrupted: invalid data size"
                )
            warn(f"MCD file '{self.path.name}' corrupted: adjusting data size")
            data_size += 1

        # Validate channel indices
        if channels is not None:
            if not all(0 <= c < num_channels for c in channels):
                raise ValueError(
                    f"Invalid channel indices: {channels}."
                    f"Must be between 0 and {num_channels - 1}."
                )

        # Calculate number of pixels based on the data size
        num_pixels = data_size // bytes_per_pixel

        # Memory-mapping the data from the file
        self._fh.seek(0)
        data = np.memmap(
            self._fh,
            dtype=np.float32,
            mode="r",
            offset=data_start_offset,
            shape=(num_pixels, num_channels + 3),
        )

        # Extract X and Y coordinates for each pixel
        xs = data[:, 0].copy().astype(int)
        ys = data[:, 1].copy().astype(int)

        # Handle region selection if specified
        if region is not None:
            if region[2] > width or region[3] > height:
                raise ValueError("Region is larger than the image")
            x_min, y_min, x_max, y_max = region
            mask = (xs >= x_min) & (xs < x_max) & (ys >= y_min) & (ys < y_max)
            xs = xs[mask] - x_min
            ys = ys[mask] - y_min
            data = data[mask]
            width = x_max - x_min
            height = y_max - y_min

        # Determine the number of selected channels
        if channels is not None:
            num_selected_channels = len(channels)
        else:
            num_selected_channels = num_channels

        # Handle empty data case
        if xs.size == 0 or ys.size == 0:
            return np.zeros((num_selected_channels, height, width), dtype=np.float32)

        # Now we either use a temporary file or in-memory NumPy array
        # for storing the image data
        if create_temp_file:
            create_temp_file.mkdir(parents=True, exist_ok=True)
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, dir=str(create_temp_file)
            )

            # Memory-map the temporary file
            img = np.memmap(
                temp_file.name,
                dtype=np.float32,
                mode="r",
                shape=(num_selected_channels, height, width),
            )
            warn(f"Temporary file created: {temp_file.name}")
        else:
            img = np.zeros((num_selected_channels, height, width), dtype=np.float32)

        # Fill the image array with the data from the memory-mapped file
        for i, c in enumerate(
            channels if channels is not None else range(num_channels)
        ):
            img[i, ys, xs] = data[:, c + 3]

        return img

    def read_slide(
        self, slide: Slide, raw: bool = False
    ) -> Union[np.ndarray, bytes, None]:
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
        data_end_offset -= 1
        if data_start_offset >= data_end_offset:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                f"invalid image data offsets for slide {slide.id}"
            )
        try:
            return self._read_image(
                data_start_offset, data_end_offset - data_start_offset, raw
            )
        except Exception as e:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                f"cannot read image for slide {slide.id}"
            ) from e

    def read_panorama(
        self, panorama: Panorama, raw: bool = False
    ) -> Union[np.ndarray, bytes, None]:
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
        if data_start_offset == data_end_offset == 0:
            return None
        data_start_offset += 161
        data_end_offset -= 1
        if data_start_offset >= data_end_offset:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                f"invalid image data offsets for panorama {panorama.id}"
            )
        try:
            return self._read_image(
                data_start_offset, data_end_offset - data_start_offset, raw
            )
        except Exception as e:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                f"cannot read image for panorama {panorama.id}"
            ) from e

    def read_before_ablation_image(
        self, acquisition: Acquisition, raw: bool = False
    ) -> Union[np.ndarray, bytes, None]:
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
            data_end_offset = int(acquisition.metadata["BeforeAblationImageEndOffset"])
        except (KeyError, ValueError) as e:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                f"cannot locate before-ablation image data "
                f"for acquisition {acquisition.id}"
            ) from e
        if data_start_offset == data_end_offset == 0:
            return None
        data_start_offset += 161
        data_end_offset -= 1
        if data_start_offset >= data_end_offset:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                f"invalid before-ablation image data offsets "
                f"for acquisition {acquisition.id}"
            )
        try:
            return self._read_image(
                data_start_offset, data_end_offset - data_start_offset, raw
            )
        except Exception as e:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                f"cannot read before-ablation image "
                f"for acquisition {acquisition.id}"
            ) from e

    def read_after_ablation_image(
        self, acquisition: Acquisition, raw: bool = False
    ) -> Union[np.ndarray, bytes, None]:
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
            data_end_offset = int(acquisition.metadata["AfterAblationImageEndOffset"])
        except (KeyError, ValueError) as e:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                f"cannot locate after-ablation image data "
                f"for acquisition {acquisition.id}"
            ) from e
        if data_start_offset == data_end_offset == 0:
            return None
        data_start_offset += 161
        data_end_offset -= 1
        if data_start_offset >= data_end_offset:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                f"invalid after-ablation image data offsets "
                f"for acquisition {acquisition.id}"
            )
        try:
            return self._read_image(
                data_start_offset, data_end_offset - data_start_offset, raw
            )
        except Exception as e:
            raise IOError(
                f"MCD file '{self.path.name}' corrupted: "
                f"cannot read after-ablation image "
                f"for acquisition {acquisition.id}"
            ) from e

    def _read_schema_xml(
        self,
        encoding: str = "utf-16-le",
        start_sub: str = "<MCDSchema",
        end_sub: str = "</MCDSchema>",
    ) -> str:
        if self._fh is None:
            raise IOError(f"MCD file '{self.path.name}' has not been opened")
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
        return data.decode(encoding=encoding)

    def _read_image(
        self, data_offset: int, data_size: int, raw: bool = False
    ) -> Union[np.ndarray, bytes]:
        if self._fh is None:
            raise IOError(f"MCD file '{self.path.name}' has not been opened")
        self._fh.seek(data_offset)
        data = self._fh.read(data_size)
        if raw:
            return data
        else:
            return imread(data)

    def __repr__(self) -> str:
        return str(self._path)
