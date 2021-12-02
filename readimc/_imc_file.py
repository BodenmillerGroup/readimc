import numpy as np

from abc import ABC, abstractmethod
from pathlib import Path


class IMCFile(ABC):
    """Shared IMC file interface"""

    def __init__(self, path: Path) -> None:
        super().__init__()
        self._path = Path(path)

    @property
    def path(self) -> Path:
        """Path to the IMC file"""
        return self._path

    @abstractmethod
    def read_acquisition(self, *kwargs) -> np.ndarray:
        """Reads IMC acquisition data as numpy array.

        :return: the acquisition data as 32-bit floating point array,
            shape: (c, y, x)
        """
        raise NotImplementedError()
