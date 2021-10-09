from dataclasses import dataclass
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import readimc.data


@dataclass(frozen=True)
class Slide:
    """Slide metadata"""

    id: int
    """Slide ID"""

    metadata: Dict[str, str]
    """Full slide metadata"""

    panoramas: List["readimc.data.Panorama"]
    """List of panoramas associated with this slide"""

    acquisitions: List["readimc.data.Acquisition"]
    """List of acquisitions associated with this slide"""

    @property
    def description(self) -> Optional[str]:
        """User-provided slide description"""
        return self.metadata.get("Description")

    @property
    def width_um(self) -> Optional[float]:
        """Slide width, in micrometers"""
        val = self.metadata.get("WidthUm")
        if val is not None:
            return float(val)
        return None

    @property
    def height_um(self) -> Optional[float]:
        """Slide height, in micrometers"""
        val = self.metadata.get("HeightUm")
        if val is not None:
            return float(val)
        return None

    def __str__(self) -> str:
        return (
            f"Slide {self.id}: {self.description or 'unnamed'} ("
            f"width = {self.width_um or '?'}um, "
            f"height = {self.height_um or '?'}um, "
            f"{len(self.panoramas)} panoramas, "
            f"{len(self.acquisitions)} acquisitions)"
        )
