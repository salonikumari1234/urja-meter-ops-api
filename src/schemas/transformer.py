from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from .meter import MeterListItem


class Transformer(BaseModel):
    model_config = ConfigDict(extra="ignore")

    code: str = Field(..., description="Unique Distribution Transformer code, e.g., DT-001")
    name: str = Field(..., description="Transformer location name, e.g., Malviya Nagar DT 1")
    feeder_code: str = Field(..., description="Upstream Feeder code, e.g., F-001")
    capacity_kva: int = Field(..., ge=1, description="Rated capacity in kVA, e.g., 63, 100, 250")
    meter_count: int = Field(default=0, ge=0, description="Number of connected meters")


class TransformerDetail(Transformer):
    meters: List[MeterListItem] = Field(default_factory=list, description="List of meters attached to this DT")
