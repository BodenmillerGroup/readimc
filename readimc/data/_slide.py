from typing import Dict, List, NamedTuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from readimc.data import Acquisition
    from readimc.data import Panorama


class Slide(NamedTuple):
    """Slide metadata"""

    id: int
    """Slide ID"""

    metadata: Dict[str, str]
    """Full slide metadata"""

    panoramas: List["Panorama"]
    """List of panoramas associated with this slide"""

    acquisitions: List["Acquisition"]
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
