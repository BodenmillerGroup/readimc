import numpy as np

from abc import ABC, abstractmethod
from pathlib import Path


class IMCFileBase(ABC):
    """Shared Fluidigm(R) IMC(TM) file interface"""

    def __init__(self, path: Path) -> None:
        super().__init__()
        self._path = Path(path)

    @property
    def path(self) -> Path:
        """Path to the Fluidigm(R) IMC(TM) file"""
        return self._path

    @abstractmethod
    def read_acquisition(self, *kwargs) -> np.ndarray:
        """Reads IMC(TM) acquisition data as numpy array.

        :return: the acquisition data as 32-bit floating point array,
            shape: (c, y, x)
        """
        raise NotImplementedError()
