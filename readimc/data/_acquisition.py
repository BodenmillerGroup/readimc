from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    import readimc.data


class AcquisitionBase(ABC):
    """Shared IMC(TM) acquisition metadata interface"""

    @property
    @abstractmethod
    def num_channels(self) -> int:
        """Number of channels"""
        raise NotImplementedError()

    @property
    @abstractmethod
    def channel_metals(self) -> Sequence[str]:
        """Symbols of metal isotopes (e.g. ``["Ag", "Ir"]``)"""
        raise NotImplementedError()

    @property
    @abstractmethod
    def channel_masses(self) -> Sequence[int]:
        """Atomic masses of metal isotopes (e.g. ``[107, 191]``)"""
        raise NotImplementedError()

    @property
    @abstractmethod
    def channel_labels(self) -> Sequence[str]:
        """Channel labels (user-provided)"""
        raise NotImplementedError()

    @property
    def channel_names(self) -> Sequence[str]:
        """Unique channel names in the format ``f"{metal}{mass}"`` (e.g.
        ``["Ag107", "Ir191"]``)"""
        return [
            f"{metal}{mass}"
            for metal, mass in zip(self.channel_metals, self.channel_masses)
        ]


@dataclass(frozen=True)
class Acquisition(AcquisitionBase):
    """IMC(TM) acquisition metadata"""

    slide: "readimc.data.Slide"
    """Parent slide"""

    id: int
    """Acquisition ID"""

    metadata: Dict[str, str]
    """Full acquisition metadata"""

    _num_channels: int
    _channel_metals: List[str]
    _channel_masses: List[int]
    _channel_labels: List[str]

    @property
    def num_channels(self) -> int:
        return self._num_channels

    @property
    def channel_metals(self) -> Sequence[str]:
        return self._channel_metals

    @property
    def channel_masses(self) -> Sequence[int]:
        return self._channel_masses

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
        if None not in (
            self.start_x_um_raw,
            self.start_x_um_corrected,
            self.width_um_raw,
            self.width_um_corrected,
        ):
            if self.width_um_corrected < self.width_um_raw:
                return self.start_x_um_corrected
            return self.start_x_um_raw
        if self.start_x_um_corrected is not None:
            return self.start_x_um_corrected
        if self.start_x_um_raw is not None:
            return self.start_x_um_raw
        return None

    @property
    def start_y_um(self) -> Optional[float]:
        "Acquisition start coordinate (y-axis), in micrometers"
        if None not in (
            self.start_y_um_raw,
            self.start_y_um_corrected,
            self.height_um_raw,
            self.height_um_corrected,
        ):
            if self.height_um_corrected < self.height_um_raw:
                return self.start_y_um_corrected
            return self.start_y_um_raw
        if self.start_y_um_corrected is not None:
            return self.start_y_um_corrected
        if self.start_x_um_raw is not None:
            return self.start_y_um_raw
        return None

    @property
    def start_x_um_raw(self) -> Optional[float]:
        """Acquisition start coordinate (x-axis) as in the raw metadata,
        in micrometers"""
        val = self.metadata.get("ROIStartXPosUm")
        if val is not None:
            return float(val)
        return None

    @property
    def start_y_um_raw(self) -> Optional[float]:
        """Acquisition start coordinate (y-axis) as in the raw metadata,
        in micrometers"""
        val = self.metadata.get("ROIStartYPosUm")
        if val is not None:
            return float(val)
        return None

    @property
    def start_x_um_corrected(self) -> Optional[float]:
        """Acquisition start coordinate (x-axis) corrected for a Fluidigm bug,
        in micrometers"""
        if self.start_x_um_raw is not None:
            return self.start_x_um_raw / 1000
        return None

    @property
    def start_y_um_corrected(self) -> Optional[float]:
        """Acquisition start coordinate (y-axis) corrected for a Fluidigm bug,
        in micrometers"""
        if self.start_y_um_raw is not None:
            return self.start_y_um_raw / 1000
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
        if None not in (self.width_um_raw, self.width_um_corrected):
            if self.width_um_corrected < self.width_um_raw:
                return self.width_um_corrected
            return self.width_um_raw
        if self.width_um_corrected is not None:
            return self.width_um_corrected
        if self.width_um_raw is not None:
            return self.width_um_raw
        return None

    @property
    def height_um(self) -> Optional[float]:
        if None not in (self.height_um_raw, self.height_um_corrected):
            if self.height_um_corrected < self.height_um_raw:
                return self.height_um_corrected
            return self.height_um_raw
        if self.height_um_corrected is not None:
            return self.height_um_corrected
        if self.height_um_raw is not None:
            return self.height_um_raw
        return None

    @property
    def width_um_raw(self) -> Optional[float]:
        """Acquisition width as in the raw metadata, in micrometers"""
        if None in (self.start_x_um_raw, self.end_x_um):
            return None
        val = abs(self.start_x_um_raw - self.end_x_um)
        if val == 0.0 and "MaxX" in self.metadata:
            val = float(self.metadata["MaxX"])
        return val

    @property
    def height_um_raw(self) -> Optional[float]:
        """Acquisition height as in the raw metadata, in micrometers"""
        if None in (self.start_y_um_raw, self.end_y_um):
            return None
        val = abs(self.start_y_um_raw - self.end_y_um)
        if val == 0.0 and "MaxY" in self.metadata:
            val = float(self.metadata["MaxY"])
        return val

    @property
    def width_um_corrected(self) -> Optional[float]:
        """Acquisition width corrected for a Fluidigm bug, in micrometers"""
        if None in (self.start_x_um_corrected, self.end_x_um):
            return None
        val = abs(self.start_x_um_corrected - self.end_x_um)
        if val == 0.0 and "MaxX" in self.metadata:
            val = float(self.metadata["MaxX"])
        return val

    @property
    def height_um_corrected(self) -> Optional[float]:
        """Acquisition height corrected for a Fluidigm bug, in micrometers"""
        if None in (self.start_y_um_corrected, self.end_y_um):
            return None
        val = abs(self.start_y_um_corrected - self.end_y_um)
        if val == 0.0 and "MaxY" in self.metadata:
            val = float(self.metadata["MaxY"])
        return val

    def __str__(self) -> str:
        return (
            f"Acquisition {self.id}: {self.description or 'unnamed'} ("
            f"x = {self.start_x_um or '?'}um, "
            f"y = {self.start_y_um or '?'}um, "
            f"width = {self.width_um or '?'}um, "
            f"height = {self.height_um or '?'}um, "
            f"{self.num_channels} channels)"
        )
