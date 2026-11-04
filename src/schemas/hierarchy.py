from typing import Dict, List
from pydantic import BaseModel, Field, ConfigDict


class HierarchyTreeNode(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., description="Entity name")
    code: str = Field(..., description="Entity unique code")
    meter_count: int = Field(default=0, description="Total meters connected within this branch")
    children: List["HierarchyTreeNode"] = Field(default_factory=list, description="Child nodes in electrical grid")


class ElectricalHierarchySummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    total_zones: int = Field(default=0)
    total_circles: int = Field(default=0)
    total_divisions: int = Field(default=0)
    total_subdivisions: int = Field(default=0)
    total_substations: int = Field(default=0)
    total_feeders: int = Field(default=0)
    total_dts: int = Field(default=0)
    total_meters: int = Field(default=0)
    tree: List[HierarchyTreeNode] = Field(default_factory=list, description="Hierarchical tree from Zone down to DTs")
