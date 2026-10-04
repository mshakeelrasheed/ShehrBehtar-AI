import os
from pathlib import Path
from config import MUNICIPAL_RULES_FILE

POLICIES = {
    "open_manhole": {
        "dept": "MCB - Water & Sanitation Branch",
        "sla": 4,
        "severity": "CRITICAL",
        "materials": "RCC precast slab (21-24 inches), retroreflective warning cones, C25 concrete mix",
        "sop": "Barricade within 2 hours. Place temporary precast cover within 4 hours. Masonry ring repair within 24 hours."
    },
    "pothole": {
        "dept": "Communication & Works (C&W) / MCB Roads",
        "sla": 48,
        "severity": "HIGH",
        "materials": "Bituminous cold-mix asphalt (50kg bags), tack coat bitumen emulsion, manual tamper",
        "sop": "Clear loose aggregate, apply tack coat emulsion, and tamp cold-mix flush with road surface."
    },
    "garbage": {
        "dept": "Bahawalpur Waste Management Company (BWMC)",
        "sla": 12,
        "severity": "MEDIUM",
        "materials": "Mini-dumper, sanitation shovel kits, lime powder (choona) 25kg bags",
        "sop": "Mechanical or manual waste lifting under Suthra Punjab SOP. Disinfect ground using lime powder within 12 hours."
    }
}

def query_municipal_policy(hazard_key: str) -> dict:
    key = hazard_key.lower().strip()
    if key in POLICIES:
        return POLICIES[key]
    return POLICIES["pothole"]