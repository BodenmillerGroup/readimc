from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    import readimc.data


class AcquisitionBase(ABC):
    """Shared IMC(TM) acquisition metadata interface"""
    @property
    @abstractmethod
    def channel_names(self) -> Sequence[str]:
        """List of channel names (i.e., metal isotopes)"""
        raise NotImplementedError()

    @property
    @abstractmethod
    def channel_labels(self) -> Sequence[str]:
        """List of channel labels (i.e., user-provided target descriptions)"""
        raise NotImplementedError()

    @property
    def num_channels(self) -> int:
        """Number of channels"""
        return len(self.channel_names)


@dataclass(frozen=True)
class Acquisition(AcquisitionBase):
    """IMC(TM) acquisition metadata"""

    slide: "readimc.data.Slide"
    """Parent slide"""

    id: int
    """Acquisition ID"""

    metadata: Dict[str, str]
    """Full acquisition metadata"""

    _channel_names: List[str]
    _channel_labels: List[str]

    @property
    def channel_names(self) -> Sequence[str]:
        return self._channel_names

    @property
    def channel_labels(self) -> Sequence[str]:
        return self._channel_labels

    @property
    def description(self) -> Optional[str]:
        """User-provided acquisition description"""
        return self.metadata.get("Description")

    @property
    def start_x_um(self) -> Optional[float]:
        """Acquisition start coordinate (x-axis), in micrometers"""
        val = self.metadata.get("ROIStartXPosUm")
        if val is not None:
            return float(val) / 1000
        return None

    @property
    def start_y_um(self) -> Optional[float]:
        """Acquisition start coordinate (y-axis), in micrometers"""
        val = self.metadata.get("ROIStartYPosUm")
        if val is not None:
            return float(val) / 1000
        return None

    @property
    def end_x_um(self) -> Optional[float]:
        """Acquisition end coordinate (x-axis), in micrometers"""
        val = self.metadata.get("ROIEndXPosUm")
        if val is not None:
            return float(val)
        return None

    @property
    def end_y_um(self) -> Optional[float]:
        """Acquisition end coordinate (y-axis), in micrometers"""
        val = self.metadata.get("ROIEndYPosUm")
        if val is not None:
            return float(val)
        return None

    @property
    def width_um(self) -> Optional[float]:
        """Acquisition width, in micrometers"""
        if None in (self.start_x_um, self.end_x_um):
            return None
        return abs(self.start_x_um - self.end_x_um)

    @property
    def height_um(self) -> Optional[float]:
        """Acquisition height, in micrometers"""
        if None in (self.start_y_um, self.end_y_um):
            return None
        return abs(self.start_y_um - self.end_y_um)

    def __str__(self) -> str:
        return (
            f"Acquisition {self.id}: {self.description or 'unnamed'} ("
            f"x = {self.start_x_um or '?'}um, "
            f"y = {self.start_y_um or '?'}um, "
            f"width = {self.width_um or '?'}um, "
            f"height = {self.height_um or '?'}um, "
            f"{self.num_channels} channels)"
        )
