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

# ---------- WORLD MAP ----------
with st.sidebar:
    st.markdown("### 🌍 World View Map")
    base_world_path = os.path.join("world data", selected_type)
    file_list = glob.glob(os.path.join(base_world_path, "*.csv"))

    available_categories = {
        os.path.basename(f)
        .replace("prod_", "")
        .replace("yield_", "")
        .replace("area_", "")
        .replace("_country.csv", "")
        .replace("_", " ")
        .title(): f
        for f in file_list
    }

    selected_file = None
    selected_world_category = None
    if available_categories:
        selected_world_category = st.selectbox("World Map Category", list(available_categories.keys()))
        selected_file = available_categories[selected_world_category]

# ---------- MAIN WORLD RENDER ----------
if selected_file:
    df_world = pd.read_csv(selected_file)
    st.subheader(f"🌐 {selected_world_category} {selected_type} Over Time")
    show_world_timelapse_map(df_world, metric_title=f"{selected_world_category} {selected_type}")
elif selected_type:  # Only warn if type was selected but no files
    st.warning("No data files found for selected type.")

# ---------- FORECAST TIMELINE ----------
if historical_df is not None and forecast_df is not None:
    # Prepare historical data
    historical_df = historical_df.rename(columns={"Total": "Value"})
    historical_df["Model"] = "Historical"

    # Prepare forecast data
    forecast_long_df = forecast_df.melt(id_vars="Year", var_name="Model", value_name="Value")

    # Combine all data
    combined_df = pd.concat([historical_df, forecast_long_df], ignore_index=True)
    combined_df = combined_df.sort_values(by=["Model", "Year"])

    # --- (KEY CHANGE) Define all models and animation years upfront ---
    all_model_names = ["Historical"] + forecast_df.columns[1:].tolist()
    all_animation_years = sorted(combined_df["Year"].unique())

    # --- Build the frames with placeholder data to ensure continuity ---
    timeline_frames = []
    for year in all_animation_years:
        # Get all data up to the current animation year
        frame_data = combined_df[combined_df["Year"] <= year].copy()
        frame_data["FrameYear"] = year

        # --- (KEY CHANGE) The robust fix:
        # Ensure a row exists for every model in this frame. If a model has no data yet,
        # add a placeholder with a null value so Plotly knows it exists.
        present_models = frame_data["Model"].unique()
        missing_models = set(all_model_names) - set(present_models)

        if missing_models:
            placeholders = []
            for model in missing_models:
                # Use the first historical year as a non-plotting anchor
                placeholders.append({
                    "Year": historical_df["Year"].min(),
                    "Model": model,
                    "Value": np.nan, # Use np.nan for a gap in the line
                    "FrameYear": year
                })
            frame_data = pd.concat([frame_data, pd.DataFrame(placeholders)], ignore_index=True)

        timeline_frames.append(frame_data)

    timeline_df = pd.concat(timeline_frames, ignore_index=True)

    # --- AXIS BOUNDS ---
    full_data_range = pd.concat([
        combined_df["Value"],
        wg_df["Value"] if wg_df is not None and not wg_df.empty else pd.Series(dtype='float64')
    ])
    y_min = full_data_range.min() * 0.95
    y_max = full_data_range.max() * 1.05
    x_min = historical_df["Year"].min()
    x_max = max(forecast_df["Year"].max(), 2047) if not forecast_df.empty else 2047

    # --- PLOT THE ANIMATED LINE CHART ---
    # The category_orders is still good practice to control the legend order.
    fig_timeline = px.line(
        timeline_df,
        x="Year",
        y="Value",
        color="Model",
        animation_frame="FrameYear",
        animation_group="Model",
        title=f"📊 Historical Data and Future Projections ({unit})",
        markers=True,
        range_y=[y_min, y_max],
        range_x=[x_min, x_max],
        category_orders={"Model": all_model_names}
    )

    # --- ADD THE STATIC WG REPORT POINTS ---
    if wg_df is not None and not wg_df.empty:
        fig_timeline.add_trace(go.Scatter(
            x=wg_df["Year"],
            y=wg_df["Value"],
            mode="markers+text",
            name="WG Report",
            marker=dict(color="red", size=12, symbol="diamond"),
            text=wg_df["Scenario"],
            textposition="top right",
            showlegend=True
        ))

    # --- CUSTOMIZE LAYOUT AND AESTHETICS ---
    fig_timeline.update_layout(
        yaxis_title=f"Value ({unit})",
        xaxis_title="Year",
        legend_title="Model/Scenario",
        font=dict(family="Poppins, sans-serif", size=12),
        title_font_size=22,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    fig_timeline.update_layout({
        'sliders': [{'currentvalue': {'prefix': 'Year: '},'pad': {'t': 20}}]
    })

    st.plotly_chart(fig_timeline, use_container_width=True)

# ---------- LOGEST GROWTH ----------
st.subheader("📈 Decade-wise Trend Growth Rate")
csv_path = os.path.join(folder_path, "historical_data.csv")
if os.path.exists(csv_path):
    fig = plot_logest_growth_from_csv(csv_path, category, conversion_multiplier)
    st.pyplot(fig)


# ---------- INDIA PULSES CHOROPLETH MAP ----------
st.markdown("---")
st.subheader("🇮🇳 India Pulses Choropleth Map Over Time")

with st.sidebar:
    st.markdown("### 🌱 Pulses Map Settings")
    season = st.selectbox("Select Season", ["Kharif", "Rabi", "Total"])

    pulse_sheets = ["Gram", "Urad", "Moong", "Masoor", "Moth", "Kulthi", "Khesari", "Peas", "Arhar"]
    pulse_type = st.selectbox("Select Pulse Type", pulse_sheets)

    metric = st.selectbox("Select Metric", ["Area", "Production", "Yield"])

try:
    # Load pulses data
    df = pd.read_excel(
        "Data/Pulses_Data.xlsx",
        sheet_name=pulse_type,
        header=1  # Header is in second row (row 2 in Excel)
    )

    # Clean columns
    df.columns = df.columns.str.strip()
    df = df.rename(columns={"States/UTs": "State"})
    df = df[df["Season"].str.lower() == season.lower()]

    # Coerce numeric
    df["Year"] = df["Year"].astype(str)
    df[metric] = pd.to_numeric(df[metric], errors="coerce")
    df = df.dropna(subset=[metric])

    df["State"] = df["State"].str.strip()
    df["State"] = df["State"].replace({
        "Orissa": "Odisha",
        "Jammu & Kashmir": "Jammu and Kashmir",
        "Delhi": "NCT of Delhi",
        # Add more if needed
    })

    # Load shapefile
    gdf = gpd.read_file("India_Shapefile/india_st.shp")
    gdf = gdf.explode(index_parts=False)  # Ensure multi-polygons handled
    gdf = gdf.to_crs(epsg=4326)

    # Clean columns
    df["State"] = df["State"].str.strip().str.upper()
    gdf["State_Name"] = gdf["State_Name"].str.strip().str.upper()

    # Map common mismatches
    df["State"] = df["State"].replace({
        "ORISSA": "ODISHA",
        "JAMMU & KASHMIR": "JAMMU AND KASHMIR",
        "DELHI": "NCT OF DELHI",
        # Add more if needed
    })

    # Merge pulses data with shapefile → for ALL years
    merged = gdf.merge(df, left_on="State_Name", right_on="State", how="left")

    # Convert merged GeoDataFrame to GeoJSON for Plotly
    merged_json = merged.__geo_interface__

    # Plotly animated choropleth
    fig = px.choropleth(
        merged,
        geojson=merged_json,
        locations="State_Name",
        featureidkey="properties.State_Name",
        color=metric,
        animation_frame="Year",  # 🎯 Adds the time slider exactly like your screenshot
        color_continuous_scale="YlOrRd",
        projection="mercator",
        hover_name="State_Name",
        hover_data={metric: True},
        title=f"{pulse_type} - {season} - {metric} Over Time"
    )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})

    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"An error occurred: {e}")


