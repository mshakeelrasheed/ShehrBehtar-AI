import folium
from folium.plugins import MarkerCluster
from typing import List, Dict, Any
from config import DEFAULT_LAT, DEFAULT_LNG

def render_civic_map(tickets: List[Dict[str, Any]], center_lat: float = DEFAULT_LAT, center_lng: float = DEFAULT_LNG) -> folium.Map:
    """
    Renders clean OpenStreetMap markers without clutter or residual direction arrows.
    """
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=13,
        tiles="OpenStreetMap",
        control_scale=True
    )

    cluster = MarkerCluster(name="Civic Incidents").add_to(m)

    for t in tickets:
        status = t.get("status", "PENDING")
        severity = t.get("severity", "MEDIUM")
        h_type = t.get("hazard_type", "Hazard")
        
        # Color & Pin logic
        if status == "RESOLVED":
            pin_color = "green"
            icon_name = "ok"
        elif "Water" in t.get("department", "") or "Manhole" in h_type:
            pin_color = "red"
            icon_name = "tint"
        elif "Waste" in t.get("department", "") or "Garbage" in h_type:
            pin_color = "orange"
            icon_name = "trash"
        else:
            pin_color = "blue"
            icon_name = "road"

        popup_content = f"""
        <div style='font-family:sans-serif; width:200px; font-size:12px;'>
            <b style='color:#0f172a; font-size:13px;'>{t.get('ticket_uid')}</b> 
            <span style='float:right; font-weight:bold; color:{"#10B981" if status=="RESOLVED" else "#EF4444"};'>{status}</span>
            <hr style='margin:4px 0;'/>
            <b>Dept:</b> {t.get('department')}<br/>
            <b>Hazard:</b> {h_type}<br/>
            <b>SLA:</b> {t.get('sla_hours')} Hours<br/>
            <span style='color:#64748b;'>{t.get('address')}</span>
        </div>
        """

        folium.Marker(
            location=[float(t["latitude"]), float(t["longitude"])],
            popup=folium.Popup(popup_content, max_width=240),
            tooltip=f"{t.get('ticket_uid')} - {t.get('department')}",
            icon=folium.Icon(color=pin_color, icon=icon_name, prefix="glyphicon")
        ).add_to(cluster)

    return m