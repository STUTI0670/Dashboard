import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from growth_analysis import plot_logest_growth_from_csv
from world_map import show_world_timelapse_map
import glob
import json
import numpy as np 
import geopandas as gpd
import matplotlib.pyplot as plt

# Page setup
st.set_page_config(layout="wide", page_title="India FoodCrop Dashboard", page_icon="🌾")

# ---------- CSS ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
}
.toggle-container {
    display: flex;
    justify-content: center;
    gap: 2rem;
    margin: 2.5rem 0 1rem;
}
.toggle-button {
    font-size: 2rem;
    padding: 1.2rem 3rem;
    border-radius: 12px;
    border: 2px solid #ccc;
    background-color: white;
    color: black;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.3s ease-in-out;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
}
.toggle-button:hover {
    transform: scale(1.1);
    background-color: #f0f0f0;
}
.toggle-button.selected {
    background-color: black;
    color: white;
    transform: scale(1.2);
}
.sidebar-title {
    background-color: white;
    padding: 1rem;
    font-size: 1.3rem;
    font-weight: 700;
    border-radius: 15px;
    margin-bottom: 1rem;
    text-align: center;
    color: #111;
}
</style>
""", unsafe_allow_html=True)

# ---------- SESSION STATE ----------
if "selected_type" not in st.session_state:
    st.session_state.selected_type = None

# ---------- SIDEBAR DROPDOWN ----------
selected_type_sidebar = st.sidebar.selectbox(
    "Select Type:",
    ["Production", "Yield", "Area"],
    index=0 if st.session_state.selected_type is None else ["Production", "Yield", "Area"].index(st.session_state.selected_type)
)

# Update session state if changed
if selected_type_sidebar != st.session_state.selected_type:
    st.session_state.selected_type = selected_type_sidebar

# ---------- INFO / STOP IF NONE SELECTED ----------
selected_type = st.session_state.selected_type
if not selected_type:
    st.markdown("<h4 style='text-align:center;'>Please select <b>Production</b>, <b>Yield</b>, or <b>Area</b> to continue.</h4>", unsafe_allow_html=True)
    st.stop()

# ---------- UNIT LOOKUP ----------
unit_lookup = {
    "Yield": {
        "Oilseeds": "Kg./hectare", "Pulses": "Kg./hectare", "Rice": "Kg./hectare", "Wheat": "Kg./hectare",
        "Coarse Cereals": "Kg./hectare", "Maize": "Kg./hectare", "Fruits": "MT/hectare", "Vegetables": "MT/hectare"
    },
    "Production": {
        "Milk": "Million Tonne", "Meat": "Million Tonne", "Eggs": "Million Numbers", "Sugar and Products": "Lakh Tonne",
        "Fruits": "'000 MT", "Vegetables": "'000 MT", "Foodgrains": "'000 Tonne", "Cereals": "'000 Tonne",
        "Pulses": "'000 Tonne", "Rice": "'000 Tonne", "Wheat": "'000 Tonne", "Coarse Cereals": "'000 Tonne", "Maize": "'000 Tonne"
    },
    "Area": {
        "Foodgrains": "Lakh hectare", "Cereals": "'000 hectare", "Fruits": "'000 hectare", "Oilseeds": "'000 hectare",
        "Pulses": "'000 hectare", "Rice": "'000 hectare", "Vegetables": "'000 hectare", "Wheat": "'000 hectare",
        "Coarse Cereals": "'000 hectare", "Maize": "'000 hectare"
    }
}
unit_conversion_map = {
    "'000 Tonne": {"Million Tonne": 0.001}, "'000 MT": {"Million Tonne": 0.001},
    "'000 hectare": {"Million hectare": 0.001}, "Lakh hectare": {"Million hectare": 0.1},
    "Million Numbers": {"Billion Numbers": 0.001}, "Kg./hectare": {"Tonne/hectare": 0.001}
}

# ---------- HEADER ----------
st.markdown(f"<h1 style='text-align:center;'>🌾 India FoodCrop Data Dashboard</h1>", unsafe_allow_html=True)

# ---------- PATH & PREFIX ----------
prefix_map = {"Production": "prod_", "Yield": "yield_", "Area": "area_"}
prefix = prefix_map[selected_type]
base_path = f"Data/{selected_type}"

# ---------- FOLDERS ----------
available_folders = [f.replace(prefix, "") for f in os.listdir(base_path) if f.startswith(prefix)]

# ---------- CATEGORY HIERARCHY ----------
category_hierarchy = {
    "Agriculture": {
        "Foodgrains": {
            "Cereals": ["Rice", "Wheat", "Cereals"],
            "Foodgrains": ["Foodgrains"],
            "Coarse Cereals": ["Maize", "Coarse Cereals"],
            "Pulses": ["Pulses"]
        },
        "Horticulture": {"Fruits": ["Fruits"], "Vegetables": ["Vegetables"]},
        "Oilseeds": {"Oilseeds": ["Oilseeds"]},
        "Commercial Crops": {"Sugar and Products": ["Sugar and Products"]}
    },
    "Allied Sectors": {
        "Animal Products": {
            "Eggs": ["Eggs"], "Milk": ["Milk"], "Meat": ["Meat"], "Marine and Inland Fish": ["Marine and Inland Fish"]
        }
    }
}

# ---------- SIDEBAR CATEGORY PICKER ----------
with st.sidebar:
    st.markdown(f"<div class='sidebar-title'>{selected_type} Categories</div>", unsafe_allow_html=True)
    sector = st.selectbox("Main Sector", list(category_hierarchy.keys()))
    sub_sector = st.selectbox("Sub-Sector", list(category_hierarchy[sector].keys()))

    def normalize(name): return name.lower().replace(" ", "").replace("_", "")
    subcat_display_to_folder = {}
    norm_available = {normalize(f): f for f in available_folders}

    for subcat_list in category_hierarchy[sector][sub_sector].values():
        for subcat in subcat_list:
            norm_subcat = normalize(subcat)
            if norm_subcat in norm_available:
                subcat_display_to_folder[subcat] = norm_available[norm_subcat]

    if not subcat_display_to_folder:
        st.error("No data available for selected sub-sector.")
        st.stop()

    category = st.selectbox("Category", list(subcat_display_to_folder.keys()))
    folder_key = subcat_display_to_folder[category]
    folder_name = f"{prefix}{folder_key}"
    folder_path = os.path.join(base_path, folder_name)

# ---------- UNIT CONVERSION PICKER ----------
unit = unit_lookup.get(selected_type, {}).get(category, "")
conversion_options = unit_conversion_map.get(unit, {})
conversion_multiplier = 1.0
if conversion_options:
    chosen_unit = st.sidebar.selectbox("Convert Unit", ["Original"] + list(conversion_options.keys()))
    if chosen_unit != "Original":
        conversion_multiplier = conversion_options[chosen_unit]
        unit = chosen_unit
# ---------- SAFE READ ----------
def safe_read(filename):
    full_path = os.path.join(folder_path, filename)
    return pd.read_csv(full_path) if os.path.exists(full_path) else None

historical_df = safe_read("historical_data.csv")
forecast_df = safe_read("forecast_data.csv")
wg_df = safe_read("wg_report.csv")

# ---------- Apply conversion ----------
if historical_df is not None:
    historical_df["Total"] *= conversion_multiplier

if forecast_df is not None:
    forecast_df.iloc[:, 1:] *= conversion_multiplier

if wg_df is not None and not wg_df.empty:
    wg_df["Value"] *= conversion_multiplier
# ---------- LOGEST GROWTH ----------
st.markdown("---")
st.subheader("📈 Decade-wise Trend Growth Rate")
csv_path = os.path.join(folder_path, "historical_data.csv")
if os.path.exists(csv_path):
    fig = plot_logest_growth_from_csv(csv_path, category, conversion_multiplier)
    st.plotly_chart(fig, use_container_width=True)
