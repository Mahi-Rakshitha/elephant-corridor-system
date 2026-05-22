import streamlit as st
import folium
import gspread
import pandas as pd

from streamlit_folium import st_folium
from folium.plugins import HeatMap

from oauth2client.service_account import (
    ServiceAccountCredentials
)

# =========================================================
# GOOGLE SHEETS CONNECTION
# =========================================================

scope = [

    "https://spreadsheets.google.com/feeds",

    "https://www.googleapis.com/auth/drive"

]

creds = ServiceAccountCredentials.from_json_keyfile_name(

    "credentials.json",

    scope

)

client = gspread.authorize(creds)

sheet = client.open(
    "ElephantCorridors"
).sheet1

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Elephant Corridor Prediction System",
    layout="wide"
)

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100%;
    }

    .stApp {
        background-color: #0b0f19;
    }

    h1, h2, h3, h4, h5, h6, p, label {
        color: white;
    }

    iframe {
        width: 100% !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================
# TITLE
# =========================================================

st.title("🐘 AI-Assisted Elephant Corridor Prediction System")

st.markdown(
    "### Dynamic Ecological Corridor Analysis for Southern India"
)

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🌿 Corridor Controls")

# =========================================================
# ECOLOGICAL FILTERS
# =========================================================

st.sidebar.header("Ecological Filters")

min_forest = st.sidebar.slider(
    "Minimum Forest Cover %",
    0,
    100,
    40
)

max_disturbance = st.sidebar.slider(
    "Maximum Human Disturbance %",
    0,
    100,
    60
)

min_slope = st.sidebar.slider(
    "Minimum Slope Suitability %",
    0,
    100,
    40
)

# =========================================================
# ADD CORRIDOR
# =========================================================

st.sidebar.markdown("---")

st.sidebar.header("➕ Add New Corridor")

corridor_name = st.sidebar.text_input(
    "Corridor Name"
)

forest = st.sidebar.slider(
    "Forest Cover %",
    0,
    100,
    75
)

water = st.sidebar.slider(
    "Water Availability %",
    0,
    100,
    70
)

slope = st.sidebar.slider(
    "Slope Suitability %",
    0,
    100,
    65
)

disturbance = st.sidebar.slider(
    "Human Disturbance %",
    0,
    100,
    30
)

st.sidebar.markdown("### Corridor Polygon Coordinates")

coord_text = st.sidebar.text_area(
    "Format: latitude,longitude",
    height=180
)

# =========================================================
# ADD CONFLICT ZONE
# =========================================================

st.sidebar.markdown("---")

st.sidebar.header("⚠ Add Conflict Zone")

conflict_lat = st.sidebar.number_input(
    "Conflict Latitude",
    value=11.75
)

conflict_lon = st.sidebar.number_input(
    "Conflict Longitude",
    value=76.55
)

# =========================================================
# COORDINATE PARSER
# =========================================================

def parse_coordinates(text):

    coords = []

    lines = text.strip().split("\n")

    for line in lines:

        try:

            lat, lon = line.split(",")

            coords.append([
                float(lat),
                float(lon)
            ])

        except:
            pass

    return coords

# =========================================================
# ADD CORRIDOR BUTTON
# =========================================================

if st.sidebar.button("Add Corridor"):

    coords = parse_coordinates(coord_text)

    if len(coords) >= 3:

        sheet.append_row([

            corridor_name,

            forest,

            water,

            slope,

            disturbance,

            str(coords)

        ])

        st.sidebar.success(
            "Corridor Added To Shared Database"
        )

    else:

        st.sidebar.error(
            "Enter at least 3 coordinates"
        )

# =========================================================
# CREATE MAP
# =========================================================

m = folium.Map(

    location=[11.6, 76.5],

    zoom_start=7,

    tiles="CartoDB dark_matter"
)

# =========================================================
# SUITABILITY FUNCTION
# =========================================================

def calculate_score(
    forest,
    water,
    slope,
    disturbance
):

    score = (
        0.4 * forest +
        0.3 * water +
        0.2 * slope -
        0.1 * disturbance
    )

    return round(score, 2)

# =========================================================
# HEATMAP DATA
# =========================================================

heat_data = []

# =========================================================
# LOAD DATA FROM GOOGLE SHEETS
# =========================================================

data = sheet.get_all_records()

# =========================================================
# DRAW USER CORRIDORS
# =========================================================

for corridor in data:

    coords = eval(corridor["coords"])

    forest = corridor["forest"]
    water = corridor["water"]
    slope = corridor["slope"]
    disturbance = corridor["disturbance"]

    if (
        forest >= min_forest and
        disturbance <= max_disturbance and
        slope >= min_slope
    ):

        score = calculate_score(
            forest,
            water,
            slope,
            disturbance
        )

        # CLASSIFICATION

        if score > 70:

            status = "Highly Suitable"
            color = "green"

        elif score > 50:

            status = "Moderately Suitable"
            color = "orange"

        else:

            status = "Unsuitable"
            color = "red"

        # =====================================================
        # POPUP
        # =====================================================

        popup_text = f"""
        <h3>🐘 {corridor['name']}</h3>

        <b>Forest Cover:</b> {forest}%<br>
        <b>Water Availability:</b> {water}%<br>
        <b>Slope Suitability:</b> {slope}%<br>
        <b>Human Disturbance:</b> {disturbance}%<br>

        <hr>

        <b>Suitability Score:</b> {score}<br>
        <b>Status:</b> {status}
        """

        # =====================================================
        # CORRIDOR POLYGON
        # =====================================================

        folium.Polygon(

            locations=coords,

            color=color,

            fill=True,

            fill_color=color,

            fill_opacity=0.5,

            weight=3,

            popup=folium.Popup(
                popup_text,
                max_width=300
            ),

            tooltip=f"🐘 {corridor['name']}"

        ).add_to(m)

        # =====================================================
        # CENTER LOCATION
        # =====================================================

        avg_lat = sum(
            [p[0] for p in coords]
        ) / len(coords)

        avg_lon = sum(
            [p[1] for p in coords]
        ) / len(coords)

        # =====================================================
        # ELEPHANT MARKER
        # =====================================================

        folium.Marker(

            location=[avg_lat, avg_lon],

            popup=f"🐘 {corridor['name']}",

            tooltip=f"🐘 {corridor['name']}",

            icon=folium.DivIcon(
                html="""
                <div style="
                    font-size:34px;
                ">
                    🐘
                </div>
                """
            )

        ).add_to(m)

        # =====================================================
        # HEATMAP
        # =====================================================

        heat_data.append([
            avg_lat,
            avg_lon,
            score
        ])

        # =====================================================
        # AI FUTURE PREDICTION
        # =====================================================

        if (
            forest > 65 and
            water > 60 and
            disturbance < 40
        ):

            predicted_coords = [

                [avg_lat + 0.12, avg_lon + 0.12],
                [avg_lat + 0.18, avg_lon + 0.20],
                [avg_lat + 0.25, avg_lon + 0.10],
                [avg_lat + 0.15, avg_lon]

            ]

            folium.Polygon(

                locations=predicted_coords,

                color="cyan",

                fill=True,

                fill_color="cyan",

                fill_opacity=0.25,

                weight=2,

                tooltip="Predicted Future Corridor",

                popup="""
                AI Predicted Future Corridor Zone
                """

            ).add_to(m)

# =========================================================
# ADD CONFLICT ZONE
# =========================================================

if st.sidebar.button("Add Conflict Zone"):

    folium.Circle(

        location=[conflict_lat, conflict_lon],

        radius=8000,

        color="red",

        fill=True,

        fill_color="red",

        fill_opacity=0.25,

        tooltip="⚠ Human-Elephant Conflict Zone"

    ).add_to(m)

# =========================================================
# HEATMAP
# =========================================================

if len(heat_data) > 0:

    HeatMap(

        heat_data,

        radius=35,

        blur=20

    ).add_to(m)

# =========================================================
# DISPLAY MAP
# =========================================================

st_folium(

    m,

    use_container_width=True,

    height=1200
)

# =========================================================
# DASHBOARD
# =========================================================

st.markdown("---")

col1, col2 = st.columns(2)

col1.metric(
    "Corridors",
    len(data)
)

col2.metric(
    "Database",
    "Google Sheets Cloud"
)

# =========================================================
# OVERVIEW
# =========================================================

st.markdown("---")

st.header("📘 System Overview")

st.write("""

Features Included:
- Shared cloud-based corridor database
- Multi-user collaborative editing
- Elephant corridor polygons
- 🐘 Elephant markers
- Heatmap visualization
- AI future corridor prediction
- Ecological suitability analysis
- Human-elephant conflict zones

AI Prediction Logic:
Future corridors are predicted when:
- Forest cover is high
- Water availability is high
- Human disturbance is low

""")