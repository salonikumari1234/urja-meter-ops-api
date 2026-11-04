from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class MeterPhase(str, Enum):
    SINGLE = "single"
    THREE = "three"


class MeterStatus(str, Enum):
    INSTALLED = "Installed"
    FAULTY = "Faulty"
    DECOMMISSIONED = "Decommissioned"


class MeterInstallType(str, Enum):
    WHOLE_CURRENT = "Whole Current"
    CT_OPERATED = "CT Operated"


class GeoCoordinates(BaseModel):
    model_config = ConfigDict(extra="ignore")

    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude coordinate")


class HierarchyNode(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., description="Descriptive name of hierarchy entity")
    code: str = Field(..., description="Unique electrical hierarchy code")


class MeterHierarchy(BaseModel):
    model_config = ConfigDict(extra="ignore")

    zone: HierarchyNode
    circle: HierarchyNode
    division: HierarchyNode
    subdivision: HierarchyNode
    substation: HierarchyNode
    feeder: HierarchyNode
    dt: HierarchyNode


class MeterListItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    meter_id: str = Field(..., description="Unique meter identifier, e.g., J100000")
    serial_no: str = Field(..., description="Meter hardware serial number, e.g., SE33962")
    make: str = Field(..., description="Manufacturer brand, e.g., HPL, Genus, Secure")
    phase_type: str = Field(..., description="Electrical phase type ('single' or 'three')")
    install_status: str = Field(..., description="Current status ('Installed', 'Faulty', 'Decommissioned')")
    install_type: Optional[str] = Field(default=None, description="Installation wiring type ('Whole Current' or 'CT Operated')")
    build: Optional[str] = Field(default=None, description="Firmware generation / build ('legacy' or 'v2')")
    dt_code: str = Field(..., description="Distribution transformer code, e.g., DT-001")
    geo: Optional[GeoCoordinates] = Field(default=None, description="GPS coordinates")


class MeterDetail(MeterListItem):
    hierarchy: Optional[MeterHierarchy] = Field(default=None, description="Complete 7-level electrical hierarchy")
