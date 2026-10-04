import urllib.request
import json
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from typing import Tuple, Optional
from config import DEFAULT_LAT, DEFAULT_LNG, DEFAULT_CITY

def _get_decimal_from_dms(dms, ref):
    degrees = dms[0]
    minutes = dms[1] / 60.0
    seconds = dms[2] / 3600.0

    if ref in ['S', 'W']:
        degrees = -degrees
        minutes = -minutes
        seconds = -seconds

    return round(float(degrees + minutes + seconds), 6)

def extract_exif_gps(image: Image.Image) -> Tuple[float, float, str]:
    """
    Extracts GPS coordinates from image EXIF metadata.
    Falls back to Bahawalpur City center if unavailable.
    """
    try:
        exif_data = image._getexif()
        if not exif_data:
            return DEFAULT_LAT, DEFAULT_LNG, f"{DEFAULT_CITY} Center (Default)"

        gps_info = {}
        for tag, value in exif_data.items():
            tag_name = TAGS.get(tag, tag)
            if tag_name == "GPSInfo":
                for t in value:
                    sub_tag = GPSTAGS.get(t, t)
                    gps_info[sub_tag] = value[t]

        if "GPSLatitude" in gps_info and "GPSLongitude" in gps_info:
            lat = _get_decimal_from_dms(gps_info["GPSLatitude"], gps_info.get("GPSLatitudeRef", "N"))
            lng = _get_decimal_from_dms(gps_info["GPSLongitude"], gps_info.get("GPSLongitudeRef", "E"))
            addr = reverse_geocode_coords(lat, lng)
            return lat, lng, addr
    except Exception as e:
        print(f"[GeoUtils EXIF Exception]: {e}")

    return DEFAULT_LAT, DEFAULT_LNG, f"{DEFAULT_CITY} Municipal Sector (Auto)"

def reverse_geocode_coords(lat: float, lng: float) -> str:
    """
    Converts (lat, lng) to a readable landmark/address using OpenStreetMap Nominatim.
    """
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&zoom=17&addressdetails=1"
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "ShehrBehtarAI-CivicPortal/1.0 (contact: mshakeelrasheed@iub.edu.pk)"}
        )
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode())
            addr_parts = data.get("address", {})
            road = addr_parts.get("road") or addr_parts.get("suburb") or addr_parts.get("neighbourhood") or "Urban Sector"
            city = addr_parts.get("city") or addr_parts.get("town") or DEFAULT_CITY
            return f"{road}, {city}"
    except Exception as e:
        print(f"[Reverse Geocode Notice]: {e}")
        return f"{DEFAULT_CITY} Sector ({lat:.4f}, {lng:.4f})"