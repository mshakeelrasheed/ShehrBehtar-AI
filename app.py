import streamlit as st
from PIL import Image
from pathlib import Path
from streamlit_folium import st_folium

try:
    from streamlit_js_eval import get_geolocation
except ImportError:
    get_geolocation = None

from config import DEFAULT_CITY, DEFAULT_LAT, DEFAULT_LNG, STATIC_DIR
from core.database import init_db, insert_ticket, get_all_tickets, mark_ticket_resolved
from core.geo_utils import extract_exif_gps, reverse_geocode_coords
from core.vision_detector import detect_civic_hazards
from core.agents.triage_agent import triage_and_route_hazards
from utils.visualizer import annotate_image_with_hazards
from utils.map_renderer import render_civic_map
from utils.charts import (
    create_department_breakdown_chart, 
    create_severity_pie_chart,
    create_timeline_trend_chart,
    filter_tickets_by_timeframe
)

# Page Configuration
st.set_page_config(
    page_title="ShehrBehtar AI | Smart Civic Ops",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database
init_db()

# Track submitted tickets in current session
if "submitted_uids" not in st.session_state:
    st.session_state.submitted_uids = []

# ==========================================
# MODERN DESIGN SYSTEM & CUSTOM STYLING
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at top right, #0f172a 0%, #020617 100%);
        color: #f8fafc;
    }

    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.75) !important;
        backdrop-filter: blur(16px);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    .hero-banner {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.75) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 22px 26px;
        margin-bottom: 22px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.35);
    }
    .hero-banner h1 {
        margin: 0;
        font-size: 25px;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-banner p {
        margin: 6px 0 0 0;
        color: #94a3b8;
        font-size: 13.5px;
    }

    .stButton>button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 8px !important;
        padding: 10px 22px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        letter-spacing: 0.3px;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35) !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5) !important;
        transform: scale(1.01);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(15, 23, 42, 0.5);
        padding: 6px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        color: #94a3b8;
        font-weight: 600;
        padding: 8px 18px;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(56, 189, 248, 0.15) !important;
        color: #38bdf8 !important;
    }

    [data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        padding: 14px 18px !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 24px !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.markdown("""
<div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
    <span style="font-size:28px;">🏙️</span>
    <div>
        <h3 style="margin:0; font-size:17px; font-weight:700; color:#f8fafc;">ShehrBehtar AI</h3>
        <p style="margin:0; font-size:11px; color:#94a3b8;">Bahawalpur Smart Ops</p>
    </div>
</div>
""", unsafe_allow_html=True)

portal_view = st.sidebar.radio(
    "Navigation Portal",
    ["📢 Citizen Portal (Report & Track)", "🛡️ Super Admin (City Command Desk)"],
    label_visibility="collapsed"
)

# ==========================================
# 1. CITIZEN PORTAL (REPORT & LIVE TRACK)
# ==========================================
if portal_view == "📢 Citizen Portal (Report & Track)":
    st.sidebar.markdown("---")
    st.sidebar.markdown("<p style='font-size:12px; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.5px;'>Aapki Reports (Live Track)</p>", unsafe_allow_html=True)
    
    if not st.session_state.submitted_uids:
        st.sidebar.caption("Is session mein abhi tak koi complaint register nahi hui.")
    else:
        all_recs = get_all_tickets()
        user_recs = [r for r in all_recs if r["ticket_uid"] in st.session_state.submitted_uids]
        
        for r in user_recs:
            is_res = r["status"] == "RESOLVED"
            badge_bg = "rgba(6, 78, 59, 0.8)" if is_res else "rgba(30, 27, 75, 0.8)"
            accent_border = "#10b981" if is_res else "#6366f1"
            status_text = "RESOLVED ✅" if is_res else "IN PROGRESS ⏳"
            
            st.sidebar.markdown(f"""
            <div style="background-color: {badge_bg}; color: #ffffff; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid {accent_border}; border: 1px solid rgba(255,255,255,0.06);">
                <div style="display:flex; justify-content:space-between; font-size:12px;">
                    <b>{r['ticket_uid']}</b>
                    <span style="font-weight:bold;">{status_text}</span>
                </div>
                <div style="font-size:12px; margin-top:4px;"><b>Dept:</b> {r['department']}</div>
                <div style="font-size:11px; opacity:0.85;"><b>SLA:</b> {r['sla_hours']} Hours</div>
                {f"<div style='font-size:11px; color:#34d399; margin-top:4px;'><b>Resolved:</b> {r['resolved_at']}</div>" if is_res else ""}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div class="hero-banner">
        <h1>Public Civic Hazard Reporting</h1>
        <p>Broken roads, open gutters, aur uncollected garbage heaps foran report karein.</p>
    </div>
    """, unsafe_allow_html=True)

    tab_report, tab_track = st.tabs(["🚀 Report New Hazard", "🔍 Search Any Ticket"])

    with tab_report:
        col_left, col_right = st.columns([1.1, 1], gap="large")

        with col_left:
            st.markdown("#### 1. Street Photographic Evidence")
            uploaded_file = st.file_uploader("Upload street photo (Max 10MB)", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

            # Demo Presets Selection
            test_samples_dir = STATIC_DIR / "test_samples"
            sample_files = list(test_samples_dir.glob("*.jpg")) + list(test_samples_dir.glob("*.png"))
            
            selected_sample = None
            chosen = "-- Quick Demo Sample --"
            if sample_files:
                preset_options = ["-- Quick Demo Sample --"] + [f.name for f in sample_files]
                chosen = st.selectbox("Quick Test Images", preset_options)
                if chosen != "-- Quick Demo Sample --":
                    selected_sample = Image.open(test_samples_dir / chosen)

            active_img = uploaded_file if uploaded_file else selected_sample
            if active_img:
                img_obj = Image.open(active_img) if uploaded_file else active_img
                st.image(img_obj, caption="Evidence Source View", width=380)

                auto_lat, auto_lng, detected_addr = extract_exif_gps(img_obj)

                st.markdown("#### 2. Geo-Location Details")

                # Mobile Browser Live Location Access
                current_lat, current_lng, current_addr = auto_lat, auto_lng, detected_addr
                if get_geolocation is not None:
                    loc = get_geolocation()
                    if loc and "coords" in loc:
                        current_lat = float(loc["coords"]["latitude"])
                        current_lng = float(loc["coords"]["longitude"])
                        current_addr = reverse_geocode_coords(current_lat, current_lng)
                        st.markdown(f"<div style='color:#34d399; font-size:13px; font-weight:700; margin-bottom:8px;'>📍 Live GPS Active ({current_lat:.4f}, {current_lng:.4f})</div>", unsafe_allow_html=True)

                selected_cat = st.selectbox(
                    "Hazard Category Selection",
                    [
                        "🤖 Auto-Detect (AI Multi-Model)",
                        "Open Gutter / Manhole (MCB Water Wing)",
                        "Road Pothole / Surface Damage (C&W Roads)",
                        "Garbage Dump / Solid Waste (BWMC)"
                    ]
                )

                c1, c2 = st.columns(2)
                with c1:
                    in_lat = st.number_input("Latitude", value=current_lat, format="%.6f")
                with c2:
                    in_lng = st.number_input("Longitude", value=current_lng, format="%.6f")
                in_addr = st.text_input("Area / Landmark", value=current_addr)

                file_hint = ""
                if uploaded_file is not None:
                    file_hint = uploaded_file.name
                elif selected_sample is not None and chosen != "-- Quick Demo Sample --":
                    file_hint = chosen

                if st.button("🚀 Analyze & Dispatch Report", type="primary"):
                    with st.spinner("AI Vision Inspector analyzing hazard..."):
                        det_res = detect_civic_hazards(
                            img_obj, 
                            filename_hint=file_hint, 
                            user_category_hint=selected_cat
                        )

                    if not det_res.hazards:
                        st.warning("No critical municipal hazard detected in this photo.")
                    else:
                        annotated = annotate_image_with_hazards(img_obj, det_res.hazards)
                        st.image(annotated, caption="Computer Vision Detection Overlay", width=380)

                        with st.spinner("Multi-Agent Policy RAG routing complaints..."):
                            tickets = triage_and_route_hazards(det_res, lat=in_lat, lng=in_lng, address=in_addr)

                            for t in tickets:
                                img_path = STATIC_DIR / f"{t.ticket_uid}.jpg"
                                annotated.save(img_path)

                                insert_ticket({
                                    "ticket_uid": t.ticket_uid,
                                    "hazard_type": t.hazard_type,
                                    "department": t.department,
                                    "severity": t.severity,
                                    "sla_hours": t.sla_hours,
                                    "hazard_score": t.hazard_score,
                                    "latitude": t.latitude,
                                    "longitude": t.longitude,
                                    "address": t.address,
                                    "notes": t.notes,
                                    "materials_needed": t.materials_needed,
                                    "image_path": str(img_path)
                                })
                                st.session_state.submitted_uids.append(t.ticket_uid)

                                st.markdown(f"""
                                <div style="background-color: rgba(6, 78, 59, 0.8); color: #ecfdf5; padding: 18px; border-radius: 10px; border-left: 6px solid #10b981; margin-bottom: 12px;">
                                    <h4 style="margin:0 0 6px 0; color:#34d399;">Ticket Generated: {t.ticket_uid}</h4>
                                    <p style="margin:0 0 4px 0;"><b>Assigned Authority:</b> {t.department}</p>
                                    <p style="margin:0; color:#a7f3d0;"><b>Mandated Resolution Window (SLA):</b> {t.sla_hours} Hours mein resolve hoga.</p>
                                </div>
                                """, unsafe_allow_html=True)
                            st.rerun()

        with col_right:
            st.markdown("#### City Live Anomaly Map")
            active_tickets = get_all_tickets("PENDING")
            st_folium(render_civic_map(active_tickets), width=580, height=520, key="cit_map")

    with tab_track:
        st.markdown("#### Track Complaint Resolution Status")
        search_uid = st.text_input("Enter Ticket Tracking ID (e.g. BW-A1B2C)", "").strip().upper()
        if search_uid:
            all_recs = get_all_tickets()
            matched = next((item for item in all_recs if item["ticket_uid"] == search_uid), None)
            if matched:
                is_resolved = matched["status"] == "RESOLVED"
                bg_color = 'rgba(6, 78, 59, 0.8)' if is_resolved else 'rgba(69, 26, 3, 0.8)'
                st.markdown(f"""
                <div style="background-color: {bg_color}; padding: 22px; border-radius: 10px; color: #ffffff; border: 1px solid rgba(255,255,255,0.08);">
                    <h3 style="margin:0;">Status: {'RESOLVED ✅' if is_resolved else 'IN PROGRESS ⏳'}</h3>
                    <p style="margin:8px 0 0 0;"><b>Department:</b> {matched['department']}</p>
                    <p style="margin:4px 0 0 0;"><b>Hazard:</b> {matched['hazard_type']}</p>
                    <p style="margin:4px 0 0 0;"><b>SLA Response Window:</b> {matched['sla_hours']} Hours</p>
                    <p style="margin:4px 0 0 0;"><b>Reported Date:</b> {matched['created_at']}</p>
                    {f"<p style='margin:4px 0 0 0; color:#34d399;'><b>Resolved At:</b> {matched['resolved_at']}</p>" if is_resolved else ""}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("No record found for this Ticket ID. Please verify the code.")

# ==========================================
# 2. SUPER ADMIN COMMAND DESK
# ==========================================
else:
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    <div style="font-size:12px; color:#94a3b8; line-height:1.6;">
        <b style="color:#f8fafc;">🏛️ Municipal Policy Standards:</b><br/>
        🔴 <b>MCB Water Wing:</b> SLA 4h (Critical)<br/>
        🟡 <b>BWMC Suthra Punjab:</b> SLA 12-24h<br/>
        🟠 <b>C&W / MCB Roads:</b> SLA 48h
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="hero-banner">
        <h1>Super Admin Command & Operations</h1>
        <p>Consolidated city-wide dispatch control across all Bahawalpur Municipal Authorities.</p>
    </div>
    """, unsafe_allow_html=True)

    all_tickets = get_all_tickets()
    pending = [t for t in all_tickets if t["status"] == "PENDING"]
    resolved = [t for t in all_tickets if t["status"] == "RESOLVED"]

    # KPIs Top Cards
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Reported", len(all_tickets))
    k1_val = sum(1 for t in pending if t["severity"] == "CRITICAL")
    k2.metric("Critical Hazards (<4h)", k1_val, delta=f"{k1_val} Actionable", delta_color="inverse")
    k3.metric("Resolved Cases", len(resolved))
    comp_rate = round((len(resolved) / max(1, len(all_tickets))) * 100, 1)
    k4.metric("City SLA Compliance", f"{comp_rate}%")

    st.markdown("---")

    # Filter Work Orders by Department
    dept_filter = st.selectbox(
        "🏢 Filter Work Orders by Department:",
        [
            "All Departments",
            "MCB - Water & Sanitation Branch",
            "Bahawalpur Waste Management Company (BWMC)",
            "Communication & Works (C&W) / MCB Roads"
        ]
    )

    filtered_tickets = all_tickets
    if dept_filter != "All Departments":
        filtered_tickets = [t for t in all_tickets if dept_filter.lower() in t["department"].lower()]

    col_map_view, col_list_view = st.columns([1.1, 1], gap="large")

    with col_map_view:
        st.markdown("#### Geospatial Overview (OpenStreetMap)")
        st_folium(render_civic_map(filtered_tickets), width=650, height=480, key="adm_map")

    with col_list_view:
        st.markdown("#### Incident Dispatch Orders")
        pending_filtered = [t for t in filtered_tickets if t["status"] == "PENDING"]
        
        if not pending_filtered:
            st.info("No pending work orders under this selection.")
        else:
            for item in pending_filtered:
                with st.expander(f"🔴 [{item['severity']}] {item['ticket_uid']} - {item['hazard_type']}", expanded=True):
                    st.write(f"**Department:** {item['department']}")
                    st.write(f"**Location:** {item['address']}")
                    st.write(f"**SLA Window:** {item['sla_hours']} Hours")
                    st.write(f"**Required Equipment:** {item['materials_needed']}")
                    st.write(f"**Action Notes:** {item['notes']}")
                    
                    if st.button("Mark Resolved & Close Ticket", key=f"btn_{item['ticket_uid']}", type="primary"):
                        mark_ticket_resolved(item['ticket_uid'])
                        st.success(f"Ticket {item['ticket_uid']} marked as RESOLVED!")
                        st.rerun()

    # =============================================================
    # 3. TEMPORAL ANALYTICS & EXECUTIVE PERFORMANCE GRAPHS
    # =============================================================
    st.markdown("---")
    
    col_analytics_header, col_time_filter = st.columns([2.2, 1])
    with col_analytics_header:
        st.markdown("#### 📊 Workload Analytics & Departmental Performance")
        st.caption("Temporal inspection, daily inflow-clearance velocity, aur departmental SLA adherence.")
    
    with col_time_filter:
        timeframe_sel = st.selectbox(
            "⏳ Temporal Horizon Filter",
            ["Last 7 Days (Weekly)", "Last 30 Days (Monthly)", "Last 365 Days (Yearly)", "All Time"],
            index=3
        )

    # Apply Time Scope Filter
    scoped_tickets = filter_tickets_by_timeframe(filtered_tickets, timeframe_sel)

    # Full-width Daily Velocity Timeline (Date-wise Inflow vs Clearance)
    st.plotly_chart(create_timeline_trend_chart(scoped_tickets), use_container_width=True)

    # Side-by-side Segmented Workload and Severity Distribution
    ch1, ch2 = st.columns(2)
    with ch1:
        st.plotly_chart(create_department_breakdown_chart(scoped_tickets), use_container_width=True)
    with ch2:
        st.plotly_chart(create_severity_pie_chart(scoped_tickets), use_container_width=True)