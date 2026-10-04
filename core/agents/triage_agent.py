import uuid
from typing import List
from config import HAZARD_CONFIG
from core.agents.state import VisionDetectionResult, ProcessedTicket
from core.agents.policy_rag import query_municipal_policy

def triage_and_route_hazards(
    detection_res: VisionDetectionResult,
    lat: float,
    lng: float,
    address: str
) -> List[ProcessedTicket]:
    """
    Guaranteed Priority-based Municipal Routing:
    1. Manhole / Sewer / Drain / Gutter / Curb Hole -> MCB - Water & Sanitation Branch
    2. Garbage / Waste / Trash / Kachra            -> Bahawalpur Waste Management Company (BWMC)
    3. Pothole / Asphalt / Road Damage             -> Communication & Works (C&W) / MCB Roads
    """
    processed_tickets: List[ProcessedTicket] = []

    for hazard in detection_res.hazards:
        h_type = (hazard.hazard_type or "").lower().strip()
        h_desc = (hazard.description or "").lower().strip()
        combined = f"{h_type} {h_desc}"

        print(f"[Triage Inspector] Detected Type: '{h_type}' | Description: '{h_desc}'")

        # PRIORITY 1: Water & Sanitation (Manhole / Gutter / Sewer / Drain)
        # Footpath par toota drain ya road ke kinare khula chamber Water & Sanitation ko hi jana chahiye
        manhole_keywords = ["manhole", "gutter", "sewer", "drain", "chamber", "culvert", "slab", "curb hole", "open hole"]
        garbage_keywords = ["garbage", "waste", "trash", "kachra", "dump", "debris", "litter", "rubbish"]

        if any(w in combined for w in manhole_keywords) or h_type == "open_manhole":
            norm_key = "open_manhole"
        # PRIORITY 2: Waste Management
        elif any(w in combined for w in garbage_keywords) or h_type == "garbage":
            norm_key = "garbage"
        # PRIORITY 3: Road Infrastructure
        else:
            norm_key = "pothole"

        policy = query_municipal_policy(norm_key)
        ticket_uid = f"BW-{uuid.uuid4().hex[:5].upper()}"

        dept = policy["dept"]
        severity = policy["severity"]
        sla = policy["sla"]
        materials = policy["materials"]
        action_note = hazard.description or policy["sop"]

        print(f"[Routing Decision] {ticket_uid} -> Norm Key: {norm_key.upper()} -> Assigned to: {dept} (SLA: {sla}h)")

        processed_tickets.append(
            ProcessedTicket(
                ticket_uid=ticket_uid,
                hazard_type=HAZARD_CONFIG.get(norm_key, {}).get("label", norm_key.title()),
                department=dept,
                severity=severity,
                sla_hours=sla,
                hazard_score=95 if severity == "CRITICAL" else (80 if severity == "HIGH" else 65),
                latitude=lat,
                longitude=lng,
                address=address,
                notes=action_note,
                materials_needed=materials
            )
        )

    return processed_tickets