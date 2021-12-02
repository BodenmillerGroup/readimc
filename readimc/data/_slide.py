from pydantic import Field
from pydantic.dataclasses import dataclass
from typing import Dict, List, Optional

from readimc.data._acquisition import Acquisition
from readimc.data._panorama import Panorama


@dataclass
class Slide:
    """Slide metadata"""

    id: int
    """Slide ID"""

    metadata: Dict[str, str]
    """Full slide metadata"""

    panoramas: List[Panorama] = Field(default_factory=list)
    """List of panoramas associated with this slide"""

    acquisitions: List[Acquisition] = Field(default_factory=list)
    """List of acquisitions associated with this slide"""

    @property
    def description(self) -> Optional[str]:
        """User-provided slide description"""
        return self.metadata.get("Description")

    @property
    def width_um(self) -> Optional[float]:
        """Slide width, in micrometers"""
        value = self.metadata.get("WidthUm")
        if value is not None:
            return float(value)
        return None

    @property
    def height_um(self) -> Optional[float]:
        """Slide height, in micrometers"""
        value = self.metadata.get("HeightUm")
        if value is not None:
            return float(value)
        return None
