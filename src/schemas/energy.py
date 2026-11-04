from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class EnergyReading(BaseModel):
    model_config = ConfigDict(extra="ignore")

    timestamp: str = Field(..., description="ISO-8601 UTC timestamp of the interval reading")
    kwh: float = Field(..., ge=0.0, description="Cumulative active energy reading in kWh")
    kvah: float = Field(..., ge=0.0, description="Cumulative apparent energy reading in kVAh")
    volt_r: float = Field(..., ge=0.0, description="Phase R voltage in Volts")


class MeterEnergyResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    meter_id: str = Field(..., description="Target meter identifier")
    readings_count: int = Field(..., ge=0, description="Total interval readings returned")
    latest_reading: Optional[EnergyReading] = Field(default=None, description="Most recent interval reading")
    readings: List[EnergyReading] = Field(default_factory=list, description="Historical interval readings")
