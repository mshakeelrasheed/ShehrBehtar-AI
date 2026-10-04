"""
Core modules for ShehrBehtar AI:
Includes database management, vision detectors, and geo utilities.
"""
from core.database import init_db, insert_ticket, get_all_tickets, mark_ticket_resolved
from core.geo_utils import extract_exif_gps
from core.vision_detector import detect_civic_hazards

__all__ = [
    "init_db",
    "insert_ticket",
    "get_all_tickets",
    "mark_ticket_resolved",
    "extract_exif_gps",
    "detect_civic_hazards",
]