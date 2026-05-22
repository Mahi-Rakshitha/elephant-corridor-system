import streamlit as st
import folium
import gspread
import pandas as pd

from folium.plugins import HeatMap
from folium.plugins import MiniMap

from streamlit_folium import st_folium

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
# SESSION STATE
# =========================================================

if "roads" not in st.session_state:
    st.session_state["roads"] = []

if "railways" not in st.session_state:
    st.session_state["railways"] = []

if "conflicts" not in st.session_state:
    st.session_state["conflicts"] = []

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

coord_text = st.sidebar.text_area(
    "Corridor Coordinates",
    height=180
)

# =========================================================
# ADD ROAD THREAT
# =========================================================

st.sidebar.markdown("---")

st.sidebar.header("🛣 Add Road Threat")

road_name = st.sidebar.text_input(
    "Road Name"
)

road_coords_text = st.sidebar.text_area(
    "Road Coordinates",
    height=120,
    key="road_coords"
)

# =========================================================
# ADD RAILWAY THREAT
# =========================================================

st.sidebar.markdown("---")

st.sidebar.header("🚆 Add Railway Threat")

rail_name = st.sidebar.text_input(
    "Railway Name"
)

rail_coords_text = st.sidebar.text_area(
    "Railway Coordinates",
    height=120,
    key="rail_coords"
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
            "Corridor Added"
        )

    else:

        st.sidebar.error(
            "Enter at least 3 coordinates"
        )

# =========================================================
# ADD ROAD BUTTON
# =========================================================

if st.sidebar.button("Add Road Threat"):

    road_coords = parse_coordinates(
        road_coords_text
    )

    if len(road_coords) >= 2:

        st.session_state["roads"].append({

            "name": road_name,

            "coords": road_coords

        })

        st.sidebar.success(
            "Road Threat Added"
        )

    else:

        st.sidebar.error(
            "Enter at least 2 coordinates"
        )

# =========================================================
# ADD RAILWAY BUTTON
# =========================================================

if st.sidebar.button("Add Railway Threat"):

    rail_coords = parse_coordinates(
        rail_coords_text
    )

    if len(rail_coords) >= 2:

        st.session_state["railways"].append({

            "name": rail_name,

            "coords": rail_coords

        })

        st.sidebar.success(
            "Railway Threat Added"
        )

    else:

        st.sidebar.error(
            "Enter at least 2 coordinates"
        )

# =========================================================
# ADD CONFLICT BUTTON
# =========================================================

if st.sidebar.button("Add Conflict Zone"):

    st.session_state["conflicts"].append([

        conflict_lat,

        conflict_lon

    ])

    st.sidebar.success(
        "Conflict Zone Added"
    )

# =========================================================
# CREATE MAP
# =========================================================

m = folium.Map(

    location=[11.6, 76.5],

    zoom_start=7,

    tiles=None
)

# =========================================================
# MAP STYLES
# =========================================================

folium.TileLayer(
    "CartoDB dark_matter"
).add_to(m)
# =========================================================
# MINIMAP
# =========================================================

minimap = MiniMap(

    toggle_display=True,

    position="bottomright",

    width=180,

    height=180,

    zoom_level_offset=-5

)

m.add_child(minimap)

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
# LOAD DATA
# =========================================================

data = sheet.get_all_records()

# =========================================================
# DRAW CORRIDORS
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

        if score > 70:

            status = "Highly Suitable"
            color = "green"

        elif score > 50:

            status = "Moderately Suitable"
            color = "orange"

        else:

            status = "Unsuitable"
            color = "red"

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

        avg_lat = sum(
            [p[0] for p in coords]
        ) / len(coords)

        avg_lon = sum(
            [p[1] for p in coords]
        ) / len(coords)

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

        heat_data.append([
            avg_lat,
            avg_lon,
            score
        ])

        # =====================================================
        # AI FUTURE PREDICTION
        # =====================================================

        if (

            forest > 70 and
            water > 65 and
            disturbance < 35 and
            slope > 55

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

                tooltip="AI Predicted Corridor",

                popup="""
                AI Future Corridor Prediction
                """

            ).add_to(m)

# =========================================================
# DRAW ROAD THREATS
# =========================================================

for road in st.session_state["roads"]:

    folium.PolyLine(

        road["coords"],

        color="yellow",

        weight=5,

        tooltip=f"🛣 {road['name']}"

    ).add_to(m)

# =========================================================
# DRAW RAILWAYS
# =========================================================

for rail in st.session_state["railways"]:

    folium.PolyLine(

        rail["coords"],

        color="white",

        weight=4,

        dash_array="10",

        tooltip=f"🚆 {rail['name']}"

    ).add_to(m)

# =========================================================
# DRAW CONFLICT ZONES
# =========================================================

for zone in st.session_state["conflicts"]:

    folium.Circle(

        location=zone,

        radius=8000,

        color="red",

        fill=True,

        fill_color="red",

        fill_opacity=0.3,

        tooltip="⚠ Conflict Zone"

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
# LEGEND
# =========================================================

legend_html = """
<div style="
position: fixed;
bottom: 50px;
left: 50px;
width: 260px;
height: 230px;
background-color: black;
border:2px solid white;
z-index:9999;
font-size:14px;
padding: 10px;
color:white;
">

<b>🌿 Corridor Legend</b><br><br>

🟩 Highly Suitable<br>
🟧 Moderately Suitable<br>
🟥 Unsuitable<br>
🟦 AI Future Corridor<br>
🟨 Road Threat Layer<br>
⬜ Railway Threat Layer<br>
🔴 Conflict Zone<br>

</div>
"""

m.get_root().html.add_child(
    folium.Element(legend_html)
)

# =========================================================
# LAYER CONTROL
# =========================================================

folium.LayerControl().add_to(m)

# =========================================================
# DISPLAY MAP
# =========================================================

map_data = st_folium(

    m,

    use_container_width=True,

    height=1200
)

# =========================================================
# CLICK LOCATION
# =========================================================

if map_data["last_clicked"]:

    st.write("Selected Location:")

    st.write(map_data["last_clicked"])

# =========================================================
# DASHBOARD
# =========================================================

st.markdown("---")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Corridors",
    len(data)
)

col2.metric(
    "Road Threats",
    len(st.session_state["roads"])
)

col3.metric(
    "Conflict Zones",
    len(st.session_state["conflicts"])
)

# =========================================================
# SYSTEM OVERVIEW
# =========================================================

st.markdown("---")

st.header("📘 System Overview")

st.write("""

Features Included:

- User-created elephant corridors
- 🐘 Elephant markers
- Real road threat layers
- Real railway threat layers
- Human-elephant conflict zones
- Heatmap visualization
- AI future corridor prediction
- Ecological suitability analysis

AI Prediction Logic:

Future corridors are predicted when:

- Forest cover is high
- Water availability is high
- Human disturbance is low

""")