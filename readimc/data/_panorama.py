from dataclasses import dataclass
from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import readimc.data


@dataclass(frozen=True)
class Panorama:
    """Panorama metadata (only for panoramas with panorama image data)"""

    slide: "readimc.data.Slide"
    """Parent slide"""

    id: int
    """Panorama ID"""

    metadata: Dict[str, str]
    """Full panorama metadata"""

    @property
    def description(self) -> Optional[str]:
        """User-provided panorama description"""
        return self.metadata.get("Description")

    @property
    def x1_um(self) -> Optional[float]:
        """Panorama coordinate 1 (x-axis), in micrometers"""
        val = self.metadata.get("SlideX1PosUm")
        if val is not None:
            return float(val)
        return None

    @property
    def y1_um(self) -> Optional[float]:
        """Panorama coordinate 1 (y-axis), in micrometers"""
        val = self.metadata.get("SlideY1PosUm")
        if val is not None:
            return float(val)
        return None

    @property
    def x2_um(self) -> Optional[float]:
        """Panorama coordinate 2 (x-axis), in micrometers"""
        val = self.metadata.get("SlideX2PosUm")
        if val is not None:
            return float(val)
        return None

    @property
    def y2_um(self) -> Optional[float]:
        """Panorama coordinate 2 (y-axis), in micrometers"""
        val = self.metadata.get("SlideY2PosUm")
        if val is not None:
            return float(val)
        return None

    @property
    def x3_um(self) -> Optional[float]:
        """Panorama coordinate 3 (x-axis), in micrometers"""
        val = self.metadata.get("SlideX3PosUm")
        if val is not None:
            return float(val)
        return None

    @property
    def y3_um(self) -> Optional[float]:
        """Panorama coordinate 3 (y-axis), in micrometers"""
        val = self.metadata.get("SlideY3PosUm")
        if val is not None:
            return float(val)
        return None

    @property
    def x4_um(self) -> Optional[float]:
        """Panorama coordinate 4 (x-axis), in micrometers"""
        val = self.metadata.get("SlideX4PosUm")
        if val is not None:
            return float(val)
        return None

    @property
    def y4_um(self) -> Optional[float]:
        """Panorama coordinate 4 (y-axis), in micrometers"""
        val = self.metadata.get("SlideY4PosUm")
        if val is not None:
            return float(val)
        return None

    @property
    def width_um(self) -> Optional[float]:
        """Panorama width, in micrometers"""
        if None not in (
            self.x1_um,
            self.y1_um,
            self.x2_um,
            self.y2_um,
            self.x3_um,
            self.y3_um,
            self.x4_um,
            self.y4_um,
        ):
            a = (self.x1_um - self.x2_um) ** 2 + (self.y1_um - self.y2_um) ** 2
            b = (self.x3_um - self.x4_um) ** 2 + (self.y3_um - self.y4_um) ** 2
            if abs(a - b) > 0.001:
                raise ValueError(
                    f"Panorama {self.id}: inconsistent image widths"
                )
            return (a ** 0.5 + b ** 0.5) / 2.0
        return None

    @property
    def height_um(self) -> Optional[float]:
        """Panorama height, in micrometers"""
        if None not in (
            self.x1_um,
            self.y1_um,
            self.x2_um,
            self.y2_um,
            self.x3_um,
            self.y3_um,
            self.x4_um,
            self.y4_um,
        ):
            a = (self.x1_um - self.x4_um) ** 2 + (self.y1_um - self.y4_um) ** 2
            b = (self.x2_um - self.x3_um) ** 2 + (self.y2_um - self.y3_um) ** 2
            if abs(a - b) > 0.001:
                raise ValueError(
                    f"Panorama {self.id}: inconsistent image heights"
                )
            return (a ** 0.5 + b ** 0.5) / 2.0
        return None

    def __str__(self) -> str:
        return (
            f"Panorama {self.id}: {self.description or 'unnamed'} ("
            f"x = {self.x1_um or '?'}um, "
            f"y = {self.y1_um or '?'}um, "
            f"width = {self.width_um or '?'}um, "
            f"height = {self.height_um or '?'}um)"
        )
