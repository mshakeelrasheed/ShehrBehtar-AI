from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DetectedHazard(BaseModel):
    hazard_type: str = Field(description="One of: open_manhole, pothole, garbage")
    box_2d: List[int] = Field(description="Normalized [ymin, xmin, ymax, xmax] scaled 0 to 1000")
    confidence: float = Field(default=0.85)
    description: str = Field(default="")

class VisionDetectionResult(BaseModel):
    hazards: List[DetectedHazard] = Field(default_factory=list)
    raw_summary: str = Field(default="")

class ProcessedTicket(BaseModel):
    ticket_uid: str
    hazard_type: str
    department: str
    severity: str
    sla_hours: int
    hazard_score: int
    latitude: float
    longitude: float
    address: str
    notes: str
    materials_needed: str
    image_path: str = ""