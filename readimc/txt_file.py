import re
from os import PathLike
from typing import List, Optional, Sequence, TextIO, Tuple, Union
from warnings import warn

import numpy as np
import pandas as pd

from .data import Acquisition, AcquisitionBase
from .imc_file import IMCFile


class TXTFile(IMCFile, AcquisitionBase):
    _CHANNEL_REGEX = re.compile(
        r"^(?P<label>.*)\((?P<metal>[a-zA-Z]+)(?P<mass>[0-9]+)[^0-9]*\)$"
    )

    def __init__(self, path: Union[str, PathLike]) -> None:
        """A class for reading IMC .txt files

        :param path: path to the IMC .txt file
        """
        super(TXTFile, self).__init__(path)
        self._fh: Optional[TextIO] = None
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

    def __enter__(self) -> "TXTFile":
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def open(self) -> None:
        """Opens the IMC .txt file for reading.

        It is good practice to use context managers whenever possible:

        .. code-block:: python

            with TXTFile("/path/to/file.txt") as f:
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
        """Closes the IMC .txt file.

        It is good practice to use context managers whenever possible:

        .. code-block:: python

            with TXTFile("/path/to/file.txt") as f:
                pass

        """
        if self._fh is not None:
            self._fh.close()
            self._fh = None

    def read_acquisition(
        self, acquisition: Optional[Acquisition] = None, strict: bool = True
    ) -> np.ndarray:
        """Reads IMC acquisition data as numpy array.

        :param acquisition: the acquisition to read (for compatibility with ``IMCFile``
            and ``MCDFile``; unused)
        :param strict: set this parameter to False to try to recover corrupted data
        :return: the acquisition data as 32-bit floating point array,
            shape: (c, y, x)
        """
        if self._fh is None:
            raise IOError(f"TXT file '{self.path.name}' has not been opened")
        self._fh.seek(0)
        df = pd.read_table(self._fh, dtype=np.float32)
        if tuple(df.columns[:3]) != (
            "Start_push",
            "End_push",
            "Pushes_duration",
        ):
            raise IOError(
                f"TXT file '{self.path.name}' corrupted: "
                "push columns not found in tabular data"
            )
        if tuple(df.columns[3:6]) != ("X", "Y", "Z"):
            raise IOError(
                f"TXT file '{self.path.name}' corrupted: "
                "XYZ channels not found in tabular data"
            )
        width, height = df[["X", "Y"]].add(1).max(axis=0).astype(int)
        if width * height != len(df.index):
            if strict:
                raise IOError(
                    f"TXT file '{self.path.name}' corrupted: "
                    "inconsistent acquisition image data size"
                )
            warn(
                f"TXT file '{self.path.name}' corrupted: "
                "inconsistent acquisition image data size"
            )
        img = np.zeros((height, width, self.num_channels), dtype=np.float32)
        img[df["Y"].astype(int), df["X"].astype(int), :] = df.values[:, 6:]
        return np.moveaxis(img, -1, 0)

    def _read_channels(self) -> Tuple[int, List[str], List[int], List[str]]:
        if self._fh is None:
            raise IOError(f"TXT file '{self.path.name}' has not been opened")
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
