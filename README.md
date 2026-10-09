# 🏙️ ShehrBehtar AI (شہر بہتر)

### Autonomous Multi-Agent Civic Triage & Real-Time Geospatial Incident Dispatch

> **ShehrBehtar AI** turns a single street photo into a routed, time-bound municipal work order. No forms, no guessing which department to contact, and no reports left sitting in the wrong queue.

<p align="center">

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-red?logo=streamlit)](https://streamlit.io/)
[![Google Gemini](https://img.shields.io/badge/Vision-Google%20Gemini-4285F4?logo=google)](https://ai.google.dev/)
[![OpenRouter](https://img.shields.io/badge/Failover-OpenRouter-6C47FF)](https://openrouter.ai/)
[![SQLite](https://img.shields.io/badge/Database-SQLite3-003B57?logo=sqlite)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

</p>

<p align="center">
  <a href="https://shehrbehtar-ai.streamlit.app">
    <strong>🚀 Live Demo</strong>
  </a>
</p>

---

## 📌 Overview

Built for the **City Smart Civic Operations Pilot**, ShehrBehtar AI was our final project for the **Generative & Agentic AI Training – Cohort 11**.

Reporting a civic hazard is harder than it should be. Residents are asked to fill in long forms and pick from department categories they may not understand. The report then often lands with the wrong office, where it waits. Broken roads, open manholes, and illegal waste heaps stay unattended, and nobody is clearly accountable for fixing them.

ShehrBehtar AI automates the whole reporting cycle:

- 📸 A citizen uploads one photo of the hazard
- 👁️ A vision model identifies what the hazard is
- 📜 A fixed municipal rulebook decides which department owns it
- ⏱️ A response deadline is assigned based on severity
- 🧰 A crew receives a list of the equipment the job needs
- 📍 The location is captured from GPS or photo metadata, so the citizen never types an address
- 🎫 The citizen receives a ticket ID and can follow the status

---

## 🎯 Problem Statement

### 1. Reporting Friction

Long forms and unclear categories discourage citizens from reporting hazards at all.

### 2. Misdirected Complaints

When a complaint reaches the wrong department, it can sit idle in a queue that was never meant to handle it. In our pilot research, we estimated that roughly 38% of complaints end up this way.

### 3. No Enforced Deadlines

Without a defined response window, even dangerous hazards such as open manholes can wait indefinitely.

### 4. Unprepared Field Crews

Crews are sometimes dispatched without the right tools or materials, which means a second trip.

### 5. No Visibility for Citizens or Leadership

Citizens cannot see whether anyone acted on their report. City leadership has no live view of where problems cluster or which departments are overloaded.

---

# 💡 Solution

ShehrBehtar AI replaces the manual complaint process with a short automated pipeline:

```text
Street Photo
     ↓
Hazard Detection
     ↓
Rulebook-Based Department Routing
     ↓
SLA Assignment
     ↓
Equipment Recommendation
     ↓
Geolocation Capture
     ↓
Work Order + Ticket ID
     ↓
Command Desk Monitoring
```

The core idea:

> **Photograph → Classify → Route → Assign → Dispatch → Track**

---

# ✨ Key Features

## 👁️ 1. Multimodal Hazard Detection

A vision model inspects the uploaded street photo and identifies:

- Road cavities and potholes
- Open or damaged manholes
- Sewer overflow and drainage ruptures
- Uncollected solid waste and illegal dumping

Results come back with bounding-box annotations so the detected hazard is clearly marked in the image.

---

## 📜 2. Deterministic Policy Triage (Rulebook RAG)

Once a hazard is identified, a fixed municipal rulebook decides which department is responsible. This step does not rely on the language model's judgment, which is why hazards are not routed to the wrong office through model hallucination.

---

## ⏱️ 3. Automated SLA Windows

Every work order is given a response deadline based on severity:

| Priority | Resolution Window |
|---|---|
| 🔴 Critical | 4 hours |
| 🟠 High | 12–24 hours |
| 🟡 Medium | 48 hours |

---

## 🧰 4. Actionable Crew Dispatch Cards

Each work order includes the equipment the crew should bring, such as cold-mix bitumen, dewatering pumps, or lime powder, so the first visit can finish the job.

---

## 📍 5. Zero-Text Geolocation

Citizens never have to type an address. The system reads:

- Native browser GPS
- EXIF coordinates from the uploaded photo
- An interactive map for manual fine-tuning when automatic detection is not precise enough

---

## 📊 6. Command Desk & Analytics

City leadership gets a live operations view with:

- Geospatial heatmaps of reported hazards
- Daily complaint inflow and clearance trends
- Departmental workload distribution
- Severity distribution across open cases

---

## 🎫 7. Public Transparency & Audit Trail

Every report gets a trackable ticket ID. Status drawers show where a case stands, so citizens can see progress instead of wondering whether anyone noticed.

---

# 🏗️ Multi-Agent Architecture

ShehrBehtar AI is built from three agents, each with one clear job, coordinated through a deterministic workflow.

```text
                  [ Citizen Street Photo ]
                            │
                            ▼
┌──────────────────────────────────────────────────────────┐
│                AGENT 01: VISION INSPECTOR                │
│  • Hazard classification and bounding-box detection      │
│  • Primary: Google Gemini Flash                          │
│  • Automatic failover: GPT-4o-mini via OpenRouter        │
└────────────────────────────┬─────────────────────────────┘
                             │ Hazard class + severity
                             ▼
┌──────────────────────────────────────────────────────────┐
│                AGENT 02: POLICY & TRIAGE                 │
│  • Rulebook mapping to MCB, BWMC, and C&W                │
│  • SLA assignment (4h / 12–24h / 48h)                    │
│  • Equipment kit recommendation                          │
└────────────────────────────┬─────────────────────────────┘
                             │ Enriched work order
                             ▼
┌──────────────────────────────────────────────────────────┐
│             AGENT 03: DISPATCH & OPERATIONS              │
│  • Reverse geocoding and Leaflet map clustering          │
│  • Persistent state in SQLite3                           │
│  • Command desk analytics and ticket tracking            │
└──────────────────────────────────────────────────────────┘
```

### Why a failover model?

If the primary vision model is unavailable or rate-limited, the system automatically switches to GPT-4o-mini through OpenRouter. Citizens can keep reporting without interruption.

---

# 🏛️ Municipal Policy Standards

| Department | Incident Scope | Priority & SLA | Standard Equipment Kit |
|---|---|---|---|
| **MCB – Water & Sanitation Branch** | Open manholes, sewer overflow, drainage ruptures | 🔴 Critical: 4 hours | Suction tanker, safety cones, dewatering pump, hazard warning tape |
| **Bahawalpur Waste Management Company (BWMC)** | Roadside waste heaps, illegal dumping | 🟠 High: 12–24 hours | Mini-dumper, sanitation shovel kits, lime powder (25 kg), protective gloves |
| **C&W / MCB Roads Department** | Potholes, structural cavities, eroded asphalt | 🟡 Medium: 48 hours | Cold-mix bitumen (50 kg), compaction roller, road cutter, 5 traffic safety cones |

---

# 🧰 Technology Stack

| Technology | Purpose |
|---|---|
| **Python 3.10+** | Core application |
| **Streamlit** | Web interface, with custom responsive CSS (glassmorphism design) |
| **Google Gemini Flash** | Primary multimodal hazard detection |
| **OpenRouter (GPT-4o-mini)** | Automatic failover for vision analysis |
| **Folium / Streamlit-Folium / Leaflet.js** | Interactive maps and hazard clustering |
| **OpenStreetMap Nominatim** | Reverse geocoding |
| **Browser Geolocation API** | Live GPS capture |
| **Pillow (PIL)** | EXIF coordinate parsing |
| **Plotly Express** | Inflow, workload, and severity analytics |
| **SQLite3** | ACID-compliant persistent storage |
| **GitHub & Streamlit Community Cloud** | Version control and deployment |

---

# 🚀 Installation & Local Setup

## 1. Prerequisites

- Python 3.10 or higher
- A Google Gemini API key and/or an OpenRouter API key

## 2. Clone the Repository

```bash
git clone https://github.com/mshakeelrasheed/ShehrBehtar-AI.git
cd ShehrBehtar-AI
```

## 3. Create a Virtual Environment

### Windows

```bash
python -m venv venv
.\venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## 5. Configure Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY="your_google_gemini_api_key"
OPENROUTER_API_KEY="your_openrouter_api_key"
```

> ⚠️ Never commit API keys to GitHub. For Streamlit Community Cloud, add them through the app's Secrets settings instead.

## 6. Run the Application

```bash
streamlit run app.py
```

Then open **http://localhost:8501** in your browser.

---

# 🧭 User Workflow

```text
1. Open the app
      ↓
2. Upload a street photo
      ↓
3. Allow GPS, or use photo EXIF / the map picker
      ↓
4. AI detects the hazard
      ↓
5. Policy engine selects department and SLA
      ↓
6. Crew dispatch card is generated
      ↓
7. Citizen receives a ticket ID
      ↓
8. Leadership monitors the case on the command desk
```

---

# 📊 Pilot Results

Figures observed during pilot testing:

| Metric | Result |
|---|---|
| ⚡ Incident-to-dispatch time | Under 5 seconds (compared with a 3–4 day manual cycle) |
| 🎯 Departmental misrouting | Eliminated through rulebook-based routing |
| ✅ SLA compliance rate | 98.5% during pilot test deployments |

---

# 🏗️ Design Principles

### Deterministic Where It Matters
Routing and deadlines come from a fixed rulebook, not from model output.

### Citizen-First
One photo should be enough. No typing, no category hunting.

### Resilient
Automatic model failover keeps the system available when one provider is not.

### Accountable
Every case has a ticket ID, a deadline, and a visible status.

### Actionable
Every work order tells the crew what to bring, not only what is wrong.

---

# 🌱 Future Development

- 📱 Mobile-first reporting experience
- 🔔 Citizen notifications when a ticket changes status
- 🏙️ Expansion to additional cities and municipal bodies
- 🗣️ Urdu-language interface and voice reporting
- 🧠 Support for more hazard categories
- 🔐 Role-based access for department staff and administrators
- 🔗 Integration with existing municipal case-management systems

---

# 🌐 Live Demo

Try the deployed application:

**[🚀 ShehrBehtar AI – Live Demo](https://shehrbehtar-ai.streamlit.app)**

---

# 👥 Team & Contributions

| Team Member | Role | Profile |
|---|---|---|
| **Muhammad Shakeel** | **Lead AI Architect** | [LinkedIn](https://www.linkedin.com/in/muhammad-shakeel-rasheed) · [GitHub](https://github.com/mshakeelrasheed) |
| **Muhammad Rafay** | **Backend & Systems Engineer** | 
| **Nazish Fatima** | **UI/UX Designer** | 
| **Anoshay Atiq** | **Product & PRD Lead** 
| **Numan Qaiser** | **Demo & Media Specialist** | 

---

# 🙏 Acknowledgements

Thank you to NCEAC, HEC Pakistan, Pakistan Engineering Council, Pak Angels, iCodeGuru, and ASPIRE Pakistan for organizing the Generative & Agentic AI Training – Cohort 11.

Special thanks to our mentors sir Dr. Zafar Shahid and sir Mohammad Anwar Khan, and to all our instructors and trainers, for guiding us from theory to deployed agentic systems.

# 📄 License

This project is licensed under the **MIT License**.

See the [LICENSE](LICENSE) file for details.

---

<p align="center">

### 🏙️ ShehrBehtar AI

**One photo. The right department. A clear deadline.**

**Built with Python • Streamlit • Google Gemini • OpenRouter • Folium • Plotly • SQLite**

⭐ **If you find ShehrBehtar AI useful, consider starring the repository.**

</p>
