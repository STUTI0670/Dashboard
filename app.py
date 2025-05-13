import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from growth_analysis import plot_logest_growth_from_csv

# Page setup
st.set_page_config(layout="wide", page_title="India FoodCrop Dashboard", page_icon="🌾")

# ---------- CUSTOM CSS --------------
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

# ---------- TOGGLE BUTTONS ----------
st.markdown('<div class="toggle-container">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.button("Production", key="prod"):
        st.session_state.selected_type = "Production"
with col2:
    if st.button("Yield", key="yield"):
        st.session_state.selected_type = "Yield"
with col3:
    if st.button("Area", key="area"):
        st.session_state.selected_type = "Area"
st.markdown('</div>', unsafe_allow_html=True)

selected_type = st.session_state.selected_type
if not selected_type:
    st.markdown("<h4 style='text-align:center;'>Please select <b>Production</b>, <b>Yield</b>, or <b>Area</b> to continue.</h4>", unsafe_allow_html=True)
    st.stop()

# ---------- HEADER ----------
st.markdown(f"<h1 style='text-align:center;'>🌾 India FoodCrop Data Dashboard</h1>", unsafe_allow_html=True)

# ---------- FILE SETUP ----------
if selected_type == "Production":
    base_path = "Data/Production"
    prefix = "prod_"
elif selected_type == "Yield":
    base_path = "Data/Yield"
    prefix = "yield_"
elif selected_type == "Area":
    base_path = "Data/Area"
    prefix = "area_"

# ---------- SIDEBAR: Hierarchical Category Selection ----------
with st.sidebar:
    st.markdown(f"<div class='sidebar-title'>{selected_type} Categories</div>", unsafe_allow_html=True)

    main_sector = st.selectbox("Select Main Sector", ["Agriculture", "Allied Sectors"])

    sub_sector_options = {
        "Agriculture": ["Foodgrains", "Oilseeds", "Horticulture", "Commercial Crops", "Spices", "Processed Products"],
        "Allied Sectors": ["Animal Husbandry", "Fisheries"]
    }
    sub_sector = st.selectbox("Select Sub-Sector", sub_sector_options[main_sector])

    category_options = {
        "Foodgrains": ["Foodgrains", "Cereals", "Pulses (Non-cereals)"],
        "Oilseeds": ["Oilseeds"],
        "Horticulture": ["Vegetables", "Fruits", "Tree Nuts"],
        "Commercial Crops": ["Sugar Crops", "Starchy/Tuber Crops", "Beverage Crops"],
        "Spices": ["Spices"],
        "Processed Products": ["Edible Oils"],
        "Animal Husbandry": ["Milk", "Meat", "Egg", "Animal Fat"],
        "Fisheries": ["Fish"]
    }
    selected_category = st.selectbox("Select Category", category_options[sub_sector])

# ---------- Folder and Data Loader ----------
folder_name = f"{prefix}{selected_category.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('-', '').replace('/', '_')}"
folder_path = os.path.join(base_path, folder_name)

def safe_read(filename):
    full_path = os.path.join(folder_path, filename)
    return pd.read_csv(full_path) if os.path.exists(full_path) else None

# ---------- LOAD DATA ----------
historical_df = safe_read("historical_data.csv")
forecast_df = safe_read("forecast_data.csv")
wg_df = safe_read("wg_report.csv")

# ---------- LOGEST GRAPH ----------
st.subheader("📈 Decade-wise Trend Growth Rate")
csv_path = os.path.join(folder_path, "historical_data.csv")
if os.path.exists(csv_path):
    fig = plot_logest_growth_from_csv(csv_path, selected_category)
    st.pyplot(fig)

# ---------- FORECAST GRAPH ----------
if historical_df is not None and forecast_df is not None:
    st.subheader("📊 Historical and Predicted Forecasts")
    fig = px.line()
    fig.add_scatter(x=historical_df["Year"], y=historical_df["Total"], mode="lines+markers", name="Historical", line=dict(color="black"))

    for col in forecast_df.columns[1:]:
        fig.add_scatter(x=forecast_df["Year"], y=forecast_df[col], mode="lines+markers", name=col)

    if wg_df is not None:
        fig.add_scatter(x=wg_df["Year"], y=wg_df["Value"], mode="markers+text", name="WG Report",
                        marker=dict(color="red", size=10),
                        text=wg_df["Scenario"], textposition="top right")

    st.plotly_chart(fig, use_container_width=True)

# ---------- PLACEHOLDER MAP ----------
st.subheader("🗺️ Interactive India Map (Coming Soon)")
fig = go.Figure(go.Choroplethmapbox(
    geojson="https://raw.githubusercontent.com/plotly/datasets/master/india_states.geojson",
    locations=[], z=[], colorscale="Viridis",
    marker_opacity=0.5, marker_line_width=0
))
fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_zoom=3.5,
    mapbox_center={"lat": 22.9734, "lon": 78.6569},
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    height=500
)
st.plotly_chart(fig, use_container_width=True)
