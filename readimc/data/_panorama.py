from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from readimc.data._acquisition import Acquisition

if TYPE_CHECKING:
    from readimc.data._slide import Slide


@dataclass
class Panorama:
    """Panorama metadata (only for panoramas with panorama image data)"""

    slide: "Slide"
    """Parent slide"""

    id: int
    """Panorama ID"""

    metadata: Dict[str, str]
    """Full panorama metadata"""

    acquisitions: List[Acquisition] = field(default_factory=list)
    """List of acquisitions associated with this panorama"""

    @property
    def description(self) -> Optional[str]:
        """User-provided panorama description"""
        return self.metadata.get("Description")

    @property
    def width_um(self) -> Optional[float]:
        """Panorama width, in micrometers"""
        if self.points_um is not None:
            (x1, y1), (x2, y2), (x3, y3), (x4, y4) = self.points_um
            w1 = ((x1 - x2) ** 2.0 + (y1 - y2) ** 2.0) ** 0.5
            w2 = ((x3 - x4) ** 2.0 + (y3 - y4) ** 2.0) ** 0.5
            if abs(w1 - w2) > 0.001:
                raise ValueError(
                    f"Panorama {self.id}: inconsistent image widths"
                )
            return (w1 + w2) / 2.0
        return None

    @property
    def height_um(self) -> Optional[float]:
        """Panorama height, in micrometers"""
        if self.points_um is not None:
            (x1, y1), (x2, y2), (x3, y3), (x4, y4) = self.points_um
            h1 = ((x1 - x4) ** 2.0 + (y1 - y4) ** 2.0) ** 0.5
            h2 = ((x2 - x3) ** 2.0 + (y2 - y3) ** 2.0) ** 0.5
            if abs(h1 - h2) > 0.001:
                raise ValueError(
                    f"Panorama {self.id}: inconsistent image heights"
                )
            return (h1 + h2) / 2.0
        return None

    @property
    def points_um(
        self,
    ) -> Optional[
        Tuple[
            Tuple[float, float],
            Tuple[float, float],
            Tuple[float, float],
            Tuple[float, float],
        ]
    ]:
        """User-provided ROI points, in micrometers

        Order: (top left, top right, bottom right, bottom left)"""
        x1 = self.metadata.get("SlideX1PosUm")
        y1 = self.metadata.get("SlideY1PosUm")
        x2 = self.metadata.get("SlideX2PosUm")
        y2 = self.metadata.get("SlideY2PosUm")
        x3 = self.metadata.get("SlideX3PosUm")
        y3 = self.metadata.get("SlideY3PosUm")
        x4 = self.metadata.get("SlideX4PosUm")
        y4 = self.metadata.get("SlideY4PosUm")
        if None not in (x1, y1, x2, y2, x3, y3, x4, y4):
            return (
                (float(x1), float(y1)),
                (float(x2), float(y2)),
                (float(x3), float(y3)),
                (float(x4), float(y4)),
            )
        return None
