import numpy as np
import re

from os import PathLike
from typing import BinaryIO, List, Optional, Sequence, Tuple, Union

import readimc
import readimc.data


class IMCTxtFile(readimc.IMCFileBase, readimc.data.AcquisitionBase):
    _CHANNEL_REGEX = re.compile(
        r"^(?P<label>.*)\((?P<metal>[a-zA-Z]+)(?P<mass>[0-9]+)[^0-9]*\)$"
    )

    def __init__(self, path: Union[str, PathLike]) -> None:
        """A class for reading Fluidigm(R) IMC(TM) TXT files

        :param path: path to the Fluidigm(R) IMC(TM) TXT file
        """
        super(IMCTxtFile, self).__init__(path)
        self._fh: Optional[BinaryIO] = None
        self._num_channels: Optional[int] = None
        self._channel_metals: Optional[List[str]] = None
        self._channel_masses: Optional[List[int]] = None
        self._channel_labels: Optional[List[str]] = None

    @property
    def num_channels(self) -> int:
        if self._num_channels is None:
            raise IOError(f"TXT file '{self.path.name}' has not been opened")
        return self._num_channels

    @property
    def channel_metals(self) -> Sequence[str]:
        if self._channel_metals is None:
            raise IOError(f"TXT file '{self.path.name}' has not been opened")
        return self._channel_metals

    @property
    def channel_masses(self) -> Sequence[int]:
        if self._channel_masses is None:
            raise IOError(f"TXT file '{self.path.name}' has not been opened")
        return self._channel_masses

    @property
    def channel_labels(self) -> Sequence[str]:
        if self._channel_labels is None:
            raise IOError(f"TXT file '{self.path.name}' has not been opened")
        return self._channel_labels

    def __enter__(self) -> "IMCTxtFile":
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def open(self) -> None:
        """Opens the Fluidigm(R) IMC(TM) TXT file for reading.

        It is good practice to use context managers whenever possible:

        .. code-block:: python

            with IMCTxtFile("/path/to/file.txt") as f:
                pass

        """
        if self._fh is not None:
            self._fh.close()
        self._fh = open(self._path, mode="r")
        (
            self._num_channels,
            self._channel_metals,
            self._channel_masses,
            self._channel_labels,
        ) = self._read_channels()

    def close(self) -> None:
        """Closes the Fluidigm(R) IMC(TM) TXT file.

        It is good practice to use context managers whenever possible:

        .. code-block:: python

            with IMCTxtFile("/path/to/file.txt") as f:
                pass

        """
        if self._fh is not None:
            self._fh.close()
            self._fh = None

    def read_acquisition(self, *args) -> np.ndarray:
        """Reads IMC(TM) acquisition data as numpy array.

        .. note::
            This function takes a variable number of arguments for
            compatibility with ``IMCMcdFile``.

        :return: the acquisition data as 32-bit floating point array,
            shape: (c, y, x)
        """
        self._fh.seek(0)
        data = np.loadtxt(
            self._fh, dtype=np.float32, delimiter="\t", skiprows=1
        )
        if data.shape[1] <= 6:
            raise IOError(
                f"TXT file '{self.path.name}' corrupted: "
                "invalid number of columns in tabular data"
            )
        width, height = np.amax(data[:, 3:5], axis=0).astype(int) + 1
        if width * height != data.shape[0]:
            raise IOError(
                f"TXT file '{self.path.name}' corrupted: "
                "inconsistent acquisition image data size"
            )
        img = np.zeros((height, width, self.num_channels), dtype=np.float32)
        img[data[:, 4].astype(int), data[:, 3].astype(int), :] = data[:, 6:]
        return np.moveaxis(img, -1, 0)

    def _read_channels(self) -> Tuple[int, List[str], List[int], List[str]]:
        self._fh.seek(0)
        columns = self._fh.readline().split("\t")
        if tuple(columns[:3]) != ("Start_push", "End_push", "Pushes_duration"):
            raise IOError(
                f"TXT file '{self.path.name}' corrupted: "
                "push columns not found in tabular data"
            )
        if tuple(columns[3:6]) != ("X", "Y", "Z"):
            raise IOError(
                f"TXT file '{self.path.name}' corrupted: "
                "XYZ channels not found in tabular data"
            )
        channel_metals: List[str] = []
        channel_masses: List[int] = []
        channel_labels: List[str] = []
        for column in columns[6:]:
            m = re.match(self._CHANNEL_REGEX, column)
            if m is None:
                raise IOError(
                    f"TXT file '{self.path.name}' corrupted: "
                    f"cannot extract channel information from text '{column}'"
                )
            channel_metals.append(m.group("metal"))
            channel_masses.append(int(m.group("mass")))
            channel_labels.append(m.group("label"))
        return len(columns[6:]), channel_metals, channel_masses, channel_labels

    def __repr__(self) -> str:
        return str(self._path)
