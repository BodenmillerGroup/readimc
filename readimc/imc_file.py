from abc import ABC, abstractmethod
from os import PathLike
from pathlib import Path
from typing import Optional, Union

import numpy as np

from .data import Acquisition


class IMCFile(ABC):
    """Shared IMC file interface"""

    def __init__(self, path: Union[str, PathLike]) -> None:
        super().__init__()
        self._path = Path(path)

    @property
    def path(self) -> Path:
        """Path to the IMC file"""
        return self._path

    @abstractmethod
    def read_acquisition(self, acquisition: Optional[Acquisition] = None) -> np.ndarray:
        """Reads IMC acquisition data as numpy array.

        :param acquisition: the acquisition to read
        :return: the acquisition data as 32-bit floating point array,
            shape: (c, y, x)
        """
        raise NotImplementedError()
