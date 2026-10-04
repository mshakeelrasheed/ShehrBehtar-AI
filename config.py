import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory Setup
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"

# Ensure runtime directories exist
DATA_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
(STATIC_DIR / "test_samples").mkdir(exist_ok=True)

# Load Environment Variables from .env
load_dotenv(BASE_DIR / ".env")

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Default Geo-Coordinates (Bahawalpur City Center)
DEFAULT_CITY = "Bahawalpur"
DEFAULT_LAT = 29.3956
DEFAULT_LNG = 71.6836

# Database Paths (Both aliases provided for compatibility)
DB_PATH = DATA_DIR / "civic_reports.db"
SQLITE_DB_PATH = DB_PATH
MUNICIPAL_RULES_FILE = DATA_DIR / "municipal_rules.txt"

# Exact Hazard Taxonomy Configuration
HAZARD_CONFIG = {
    "open_manhole": {
        "label": "Open Gutter / Missing Manhole Cover",
        "default_dept": "MCB - Water & Sanitation Branch",
        "sla_hours": 4,
        "severity": "CRITICAL",
        "color": "#EF4444"
    },
    "garbage": {
        "label": "Roadside Solid Waste / Garbage Dump",
        "default_dept": "Bahawalpur Waste Management Company (BWMC)",
        "sla_hours": 12,
        "severity": "MEDIUM",
        "color": "#F59E0B"
    },
    "pothole": {
        "label": "Road Pothole / Asphalt Cavity",
        "default_dept": "Communication & Works (C&W) / MCB Roads",
        "sla_hours": 48,
        "severity": "HIGH",
        "color": "#3B82F6"
    }
}