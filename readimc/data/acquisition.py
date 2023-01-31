import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional, Sequence, Tuple

import numpy as np

if TYPE_CHECKING:
    from readimc.data.panorama import Panorama
    from readimc.data.slide import Slide


class AcquisitionBase(ABC):
    """Shared IMC acquisition metadata interface"""

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
            f"{channel_metal}{channel_mass}"
            for channel_metal, channel_mass in zip(
                self.channel_metals, self.channel_masses
            )
        ]


@dataclass
class Acquisition(AcquisitionBase):
    """IMC acquisition metadata"""

    slide: "Slide"
    """Parent slide"""

    panorama: Optional["Panorama"]
    """Associated panorama"""

    id: int
    """Acquisition ID"""

    roi_points_um: Optional[
        Tuple[
            Tuple[float, float],
            Tuple[float, float],
            Tuple[float, float],
            Tuple[float, float],
        ]
    ]
    """User-provided ROI points, in micrometers

    Order: (top left, top right, bottom right, bottom left)"""

    metadata: Dict[str, str]
    """Full acquisition metadata"""

    _num_channels: int
    _channel_metals: List[str] = field(default_factory=list)
    _channel_masses: List[int] = field(default_factory=list)
    _channel_labels: List[str] = field(default_factory=list)

    @property
    def description(self) -> Optional[str]:
        """User-provided acquisition description"""
        return self.metadata.get("Description")

    @property
    def width_px(self) -> Optional[int]:
        """Acquisition width, in pixels"""
        value = self.metadata.get("MaxX")
        if value is not None:
            return int(value)
        return None

    @property
    def height_px(self) -> Optional[int]:
        """Acquisition height, in pixels"""
        value = self.metadata.get("MaxY")
        if value is not None:
            return int(value)
        return None

    @property
    def pixel_size_x_um(self) -> Optional[float]:
        """Width of a single pixel, in micrometers"""
        value = self.metadata.get("AblationDistanceBetweenShotsX")
        if value is not None:
            return float(value)
        return None

    @property
    def pixel_size_y_um(self) -> Optional[float]:
        """Height of a single pixel, in micrometers"""
        value = self.metadata.get("AblationDistanceBetweenShotsY")
        if value is not None:
            return float(value)
        return None

    @property
    def width_um(self) -> Optional[float]:
        """Acquisition width, in micrometers"""
        if self.width_px is not None and self.pixel_size_x_um is not None:
            return self.width_px * self.pixel_size_x_um
        return None

    @property
    def height_um(self) -> Optional[float]:
        """Acquisition height, in micrometers"""
        if self.height_px is not None and self.pixel_size_y_um is not None:
            return self.height_px * self.pixel_size_y_um
        return None

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
    def roi_coords_um(
        self,
    ) -> Optional[
        Tuple[
            Tuple[float, float],
            Tuple[float, float],
            Tuple[float, float],
            Tuple[float, float],
        ]
    ]:
        """ROI stage coordinates, in micrometers

        Order: (top left, top right, bottom right, bottom left)"""
        x1_str = self.metadata.get("ROIStartXPosUm")
        y1_str = self.metadata.get("ROIStartYPosUm")
        x3_str = self.metadata.get("ROIEndXPosUm")
        y3_str = self.metadata.get("ROIEndYPosUm")
        if (
            x1_str != x3_str
            and y1_str != y3_str
            and x1_str is not None
            and y1_str is not None
            and x3_str is not None
            and y3_str is not None
            and self.width_um is not None
            and self.height_um is not None
        ):
            x1, y1 = float(x1_str), float(y1_str)
            x3, y3 = float(x3_str), float(y3_str)
            # fix Fluidigm bug, where start positions are multiplied by 1000
            if abs(x1 / 1000.0 - x3) < abs(x1 - x3):
                x1 /= 1000.0
            if abs(y1 / 1000.0 - y3) < abs(y1 - y3):
                y1 /= 1000.0
            # calculate counter-clockwise rotation angle, in radians
            rotated_main_diag_angle = np.arctan2(y1 - y3, x1 - x3)
            main_diag_angle = np.arctan2(self.height_um, -self.width_um)
            angle = rotated_main_diag_angle - main_diag_angle
            # calculate missing points (generative approach)
            x2, y2 = self.width_um / 2.0, self.height_um / 2.0
            x4, y4 = -self.width_um / 2.0, -self.height_um / 2.0
            x2, y2 = (
                math.cos(angle) * x2 - math.sin(angle) * y2 + (x1 + x3) / 2.0,
                math.sin(angle) * x2 + math.cos(angle) * y2 + (y1 + y3) / 2.0,
            )
            x4, y4 = (
                math.cos(angle) * x4 - math.sin(angle) * y4 + (x1 + x3) / 2.0,
                math.sin(angle) * x4 + math.cos(angle) * y4 + (y1 + y3) / 2.0,
            )
            return ((x1, y1), (x2, y2), (x3, y3), (x4, y4))
        return None
