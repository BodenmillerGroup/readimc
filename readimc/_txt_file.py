import numpy as np
import re

from os import PathLike
from pathlib import Path
from typing import BinaryIO, List, Optional, Sequence, Tuple, Union


class TXTFile:
    def __init__(self, path: Union[str, PathLike]) -> None:
        """A class for reading Fluidigm(R) TXT files

        :param path: path to the Fluidigm(R) TXT file
        """
        self._path = Path(path)
        self._fh: Optional[BinaryIO] = None
        self._channel_names: Optional[List[str]] = None
        self._channel_labels: Optional[List[str]] = None

    @property
    def path(self) -> Path:
        """Path to the Fluidigm(R) TXT file"""
        return self._path

    @property
    def channel_names(self) -> Sequence[str]:
        """List of channel names (i.e., metal isotopes)"""
        if self._channel_names is None:
            raise IOError(f"TXT file '{self.path.name}' has not been opened")
        return self._channel_names

    @property
    def channel_labels(self) -> Sequence[str]:
        """List of channel labels (i.e., user-provided target descriptions)"""
        if self._channel_labels is None:
            raise IOError(f"TXT file '{self.path.name}' has not been opened")
        return self._channel_labels

    @property
    def num_channels(self) -> int:
        """Number of channels"""
        if self._channel_names is None:
            raise IOError(f"TXT file '{self.path.name}' has not been opened")
        return len(self._channel_names)

    def __enter__(self) -> "TXTFile":
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def open(self) -> None:
        """Opens the Fluidigm(R) TXT file for reading.

        It is good practice to use context managers whenever possible:

        .. code-block:: python

            with TXTFile("/path/to/file.txt") as f:
                pass

        """
        if self._fh is not None:
            self._fh.close()
        self._fh = open(self._path, mode="r")
        self._channel_names, self._channel_labels = self._read_channels()

    def close(self) -> None:
        """Closes the Fluidigm(R) TXT file.

        It is good practice to use context managers whenever possible:

        .. code-block:: python

            with TXTFile("/path/to/file.txt") as f:
                pass

        """
        if self._fh is not None:
            self._fh.close()
            self._fh = None
        self._channel_names = None
        self._channel_labels = None

    def read_acquisition(self, *args) -> np.ndarray:
        """Reads IMC(TM) acquisition data as numpy array.

        .. note::
            This function takes a variable number of arguments for
            compatibility with ``MCDFile``.

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

    def _read_channels(self) -> Tuple[List[str], List[str]]:
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
        channel_names = []
        channel_labels = []
        for column in columns[6:]:
            channel_name, channel_label = self._parse_channel(column)
            channel_names.append(channel_name)
            channel_labels.append(channel_label)
        return channel_names, channel_labels

    def _parse_channel(self, column: str) -> Tuple[str, str]:
        m = re.match(
            r"^(?P<label>.*)\((?P<metal>[a-zA-Z]*)(?P<mass>[0-9]*)[^0-9]*\)$",
            column,
        )
        if m is None:
            raise IOError(
                f"TXT file '{self.path.name}' corrupted: "
                f"cannot extract channel name and label from text '{column}'"
            )
        channel_name = f"{m.group('metal')}({m.group('mass')})"
        channel_label = m.group("label")
        return channel_name, channel_label

    def __repr__(self) -> str:
        return str(self._path)
