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


# ---------- INDIA PULSES CHOROPLETH MAP ----------
st.markdown("---")
st.subheader("🇮🇳 India Pulses Choropleth Map Over Time")

with st.sidebar:
    st.markdown("---")
    st.markdown("### 🌱 Pulses Map Settings")
    season = st.selectbox("Select Season", ["Kharif", "Rabi", "Total"])

    pulse_sheets = ["Gram", "Urad", "Moong", "Masoor", "Moth", "Kulthi", "Khesari", "Peas", "Arhar"]
    pulse_type = st.selectbox("Select Pulse Type", pulse_sheets)

    metric = st.selectbox("Select Metric", ["Area", "Production", "Yield"])

try:
    
    df = pd.read_excel(
        "Data/Pulses_Data.xlsx",
        sheet_name=pulse_type,
        header=1  # Header is in second row (row 2 in Excel)
    )

    # Remove any extra spaces in column names (important!!)
    df.columns = df.columns.str.strip()

    # Rename "States/UTs" → "State"
    df = df.rename(columns={"States/UTs": "State"})

    # Filter season-wise
    df = df[df["Season"].str.lower() == season.lower()]

    # Coerce numeric
    df["Year"] = df["Year"].astype(str)
    df[metric] = pd.to_numeric(df[metric], errors="coerce")
    df = df.dropna(subset=[metric])

    df["State"] = df["State"].str.strip()
    df["State"] = df["State"].replace({
        "Orissa": "Odisha",
        "Jammu & Kashmir": "Jammu and Kashmir",
        "Chhattisgarh": "Chhattishgarh",
        "Telangana": "Telengana",
        "Tamil Nadu": "Tamilnadu",
        "Kerela": "Kerala",
        "Andaman & Nicobar Islands": "Andaman & Nicobar"
    
    })

    selected_year = st.sidebar.selectbox("Select Year", sorted(df["Year"].unique()))

    df_selected_year = df[df["Year"] == selected_year]

    # Load shapefile
    gdf = gpd.read_file("India_Shapefile/india_st.shp")

    # Clean columns → very important!
    df_selected_year["State"] = df_selected_year["State"].str.strip().str.upper()
    gdf["State_Name"] = gdf["State_Name"].str.strip().str.upper()

    # Optional → map common name mismatches
    df_selected_year["State"] = df_selected_year["State"].replace({
        "Orissa": "Odisha",
        "Jammu & Kashmir": "Jammu and Kashmir",
        "Chhattisgarh": "Chhattishgarh",
        "Telangana": "Telengana",
        "Tamil Nadu": "Tamilnadu",
        "Kerela": "Kerala",
        "Andaman & Nicobar Islands": "Andaman & Nicobar"
        
    })

    # Merge Shapefile with selected year df
    merged = gdf.merge(df_selected_year, left_on="State_Name", right_on="State", how="left")

    # Plot India map
    fig, ax = plt.subplots(1, 1, figsize=(10, 12))
    merged.plot(
        column=metric,
        ax=ax,
        legend=True,
        cmap='YlOrRd',
        edgecolor='black',
        missing_kwds={"color": "white", "edgecolor": "black"}
    )

    plt.title(f"{pulse_type} - {season} - {metric} in {selected_year}")
    st.pyplot(fig)

except Exception as e:
    st.error(f"An error occurred: {e}")


# ---------- STATE MAP VIEW ----------

# Load full India District shapefile (load once → top of file / cache)
@st.cache_data
def load_india_districts_shapefile():
    gdf = gpd.read_file("India_Shapefile/State/2011_Dist.shp")
    gdf = gdf.set_crs(epsg=4326, inplace=False)
    return gdf

STATE_NAME_CORRECTIONS = {
    "Orissa": "Odisha",
    "Jammu & Kashmir": "Jammu and Kashmir",
    "Chhattisgarh": "Chhattishgarh",
    "Telangana": "Telengana",
    "Tamil Nadu": "Tamilnadu",
    "Kerela": "Kerala",
    "Andaman & Nicobar Islands": "Andaman & Nicobar",
    "Arunachal Pradesh": "Arunanchal Pradesh",
    "Dadra & Nagar Haveli": "Dadara & Nagar Havelli",
    "India": None,  # Special handling → we don't want user to select "India" in district map!
    "Delhi": "NCT of Delhi"
}


gdf_districts = load_india_districts_shapefile()
gdf_districts["ST_NM"] = gdf_districts["ST_NM"].replace(STATE_NAME_CORRECTIONS)
gdf_districts["ST_NM"] = gdf_districts["ST_NM"].str.strip().str.upper()

# Sidebar: State Map View
st.sidebar.markdown("---")
st.sidebar.markdown("### 🗺️ State Map View")

# Dynamic State Map View dropdown

# Extract available states in current df_selected_year
available_states = df_selected_year["State"].str.upper().unique().tolist()

# Dropdown options → dynamic + "None" on top
state_options = ["None"] + sorted(available_states)

selected_state_map = st.sidebar.selectbox("Select State for State Map", state_options)

# Auto detect STATE column
state_col = None
for col in gdf_districts.columns:
    if "STATE" in col.upper() or "ST_NM" in col.upper():
        state_col = col
        break

# Auto detect DISTRICT column
district_col = None
for col in gdf_districts.columns:
    if "DISTRICT" in col.upper() or "DIST_NAME" in col.upper() or "DIST_NM" in col.upper():
        district_col = col
        break

# Debug: show all unique state names from district shapefile
#st.write("States in shapefile (after replacement and uppercasing):")
#st.write(sorted(gdf_districts[state_col].unique().tolist()))

#st.write("States in Pulses DataFrame (df_selected_year):")
#st.write(sorted(df_selected_year["State"].str.upper().unique().tolist()))


# Proceed only if valid state selected
if selected_state_map != "None":

    # Safety check
    if state_col is None or district_col is None:
        st.error("Could not detect STATE or DISTRICT column in shapefile!")
    else:
        # Normalize function: remove spaces, convert to upper
        def normalize_state_name(s):
            return s.upper().replace(" ", "")

        # Filter for selected state safely
        state_gdf = gdf_districts[gdf_districts[state_col].apply(normalize_state_name) == normalize_state_name(selected_state_map)]


        # Optional: explode in case MultiPolygon present
        state_gdf = state_gdf.explode(index_parts=False)

        # Prepare df_selected_year → selected state row
        state_row = df_selected_year[df_selected_year["State"].str.upper() == selected_state_map.upper()]

        if state_row.empty:
            st.warning(f"No data available for {selected_state_map} for {season} - {pulse_type} - {metric} in selected year.")
        else:
            # Extract actual state value
            state_total_value = state_row[metric].values[0]

            # Prepare dummy values per district
            districts = state_gdf[district_col].tolist()
            n_districts = len(districts)

            # Random proportions summing to 1
            proportions = np.random.dirichlet(np.ones(n_districts))
            dummy_values = proportions * state_total_value

            # Assign dummy values to GeoDataFrame
            state_gdf["Dummy_Value"] = dummy_values
            state_gdf["District"] = state_gdf[district_col]

            # Plot State district map
            st.markdown(f"### 📍 {selected_state_map} District Map - {metric} ({season}, {pulse_type})")

            fig2, ax2 = plt.subplots(1, 1, figsize=(8, 10))
            state_gdf.plot(
                column="Dummy_Value",
                ax=ax2,
                legend=True,
                cmap='YlOrRd',
                edgecolor='black',
                missing_kwds={"color": "white", "edgecolor": "black"}
            )
            plt.title(f"{selected_state_map} District Map - {metric} ({season}, {pulse_type})", fontsize=14)

            # Plot district names only once per district
            unique_districts = state_gdf.drop_duplicates(subset="District")

            for idx, row in unique_districts.iterrows():
                centroid = row["geometry"].centroid
                ax2.text(centroid.x, centroid.y, row["District"], fontsize=8, ha='center')

            st.pyplot(fig2)

            # ---------- STATE-WISE ANIMATED HISTORICAL PLOT ----------
            if not state_row.empty:
                #st.markdown("---")
                st.markdown(f"### Animated Historical Trend for {selected_state_map}")

                #
                # Filter the main dataframe for the selected state across ALL available years
                state_historical_df = df[df["State"].str.upper() == selected_state_map.upper()].copy()
                state_historical_df['Year'] = pd.to_numeric(state_historical_df['Year'].astype(str).str.split('-').str[0]) # <--- USE THIS NEW LINE
                state_historical_df = state_historical_df.sort_values("Year")
                #

                # Define units for the pulse metrics for clearer axis labels
                pulse_units = {
                    "Area": "'000 Hectare",
                    "Production": "'000 Tonne",
                    "Yield": "Kg/Hectare"
                }
                y_axis_title = f"{metric} ({pulse_units.get(metric, '')})"

                # Proceed only if there's data to animate
                if not state_historical_df.empty and state_historical_df[metric].notna().any():
                    
                    # --- Prepare data for animation ---
                    # This creates a cumulative dataset for each year, which is necessary for the animation.
                    all_years = sorted(state_historical_df["Year"].unique())
                    animation_frames = []

                    for year in all_years:
                        frame_data = state_historical_df[state_historical_df["Year"] <= year].copy()
                        frame_data["FrameYear"] = year  # This column drives the animation
                        animation_frames.append(frame_data)
                    
                    animated_state_df = pd.concat(animation_frames, ignore_index=True)

                    # --- Define axis bounds for a stable animation view ---
                    y_min_state = state_historical_df[metric].min() * 0.95
                    y_max_state = state_historical_df[metric].max() * 1.05
                    x_min_state = state_historical_df["Year"].min()
                    x_max_state = state_historical_df["Year"].max()

                    # --- Create the animated line plot ---
                    fig_state_trend = px.line(
                        animated_state_df,
                        x="Year",
                        y=metric,
                        animation_frame="FrameYear",   # Use the frame column to animate
                        animation_group="State",       # Ensures the line is continuous
                        title=f"Animated Trend of {metric} for {pulse_type} ({season}) in {selected_state_map}",
                        markers=True,
                        labels={"Year": "Year", metric: y_axis_title, "FrameYear": "Year"},
                        range_y=[y_min_state, y_max_state],
                        range_x=[x_min_state, x_max_state]
                    )

                    # --- Customize Layout and Animation Controls ---
                    fig_state_trend.update_layout(
                        yaxis_title=y_axis_title,
                        xaxis_title="Year",
                        font=dict(family="Poppins, sans-serif", size=12),
                        title_font_size=18,
                        legend_title="Metric",
                        sliders=[{
                            'currentvalue': {'prefix': 'Year: '},
                            'pad': {'t': 20}
                        }],
                        updatemenus=[{
                            'type': 'buttons',
                            'showactive': False,
                            'x': 0.05,
                            'y': -0.15,
                            'buttons': [{
                                'label': 'Play',
                                'method': 'animate',
                                'args': [None, {
                                    'frame': {'duration': 10, 'redraw': True},  # << faster animation (300 ms per frame)
                                    'fromcurrent': True,
                                    'transition': {'duration': 1}
                                }]
                            }, {
                            'label': 'Pause',
                            'method': 'animate',
                            'args': [[None], {
                                'frame': {'duration': 0, 'redraw': False},
                                'mode': 'immediate',
                                'transition': {'duration': 0}
                            }]
                            }]
                        }]
                    )
                    
                    # Customize the appearance of the animation slider
                    fig_state_trend.update_layout({
                        'sliders': [{'currentvalue': {'prefix': 'Year: '}, 'pad': {'t': 20}}]
                    })

                    st.plotly_chart(fig_state_trend, use_container_width=True)
                else:
                    st.warning(f"No historical data with values for '{metric}' is available to plot a trend for {selected_state_map}.")




# ---------- FULL INDIA DISTRICT MAP ----------

st.markdown("---")
st.subheader("🇮🇳 Full India District Map View (Fabricated Values)")

# Auto detect STATE and DISTRICT columns
state_col = None
district_col = None
for col in gdf_districts.columns:
    if "STATE" in col.upper() or "ST_NM" in col.upper():
        state_col = col
    if "DISTRICT" in col.upper() or "DIST_NAME" in col.upper() or "DIST_NM" in col.upper():
        district_col = col

# Check
if state_col is None or district_col is None:
    st.error("Could not detect STATE or DISTRICT column in shapefile!")
else:
    # Prepare a copy of gdf_districts to avoid inplace modification
    gdf_districts_full = gdf_districts.copy()

    # Prepare Dummy_Value column
    gdf_districts_full["Dummy_Value"] = 0.0

    # Process each state in df_selected_year
    for state_name in df_selected_year["State"].unique():
        state_name_upper = state_name.strip().upper()

        # Match in shapefile with normalization
        def normalize_state_name(s):
            return s.upper().replace(" ", "")

        mask = gdf_districts_full[state_col].apply(normalize_state_name) == normalize_state_name(state_name_upper)
        state_gdf = gdf_districts_full[mask]

        # If no matching districts → skip
        if state_gdf.empty:
            continue

        # Get state total value from df_selected_year
        state_row = df_selected_year[df_selected_year["State"].str.upper() == state_name_upper]
        if state_row.empty:
            continue

        state_total_value = state_row[metric].values[0]

        # Fabricate values across districts
        districts = state_gdf[district_col].unique().tolist()
        n_districts = len(districts)

        proportions = np.random.dirichlet(np.ones(n_districts))
        dummy_values = proportions * state_total_value

        # Assign fabricated values to Dummy_Value column
        for i, district_name in enumerate(districts):
            gdf_districts_full.loc[
                (mask) & (gdf_districts_full[district_col] == district_name),
                "Dummy_Value"
            ] = dummy_values[i]

    # Plot the full India district map
    fig_full, ax_full = plt.subplots(1, 1, figsize=(12, 14))
    gdf_districts_full.plot(
        column="Dummy_Value",
        ax=ax_full,
        legend=True,
        cmap='YlOrRd',
        edgecolor='black',
        missing_kwds={"color": "white", "edgecolor": "black"}
    )
    ax_full.set_title(f"Full India District Map - {metric} ({season}, {pulse_type}, {selected_year})", fontsize=16)

    st.pyplot(fig_full)

# ---------- DISTRICT-WISE LINE PLOT (Random Historical Data) ----------
# ---------- DISTRICT-WISE ANIMATED HISTORICAL PLOT (RANDOM VALUES) ----------
st.markdown("---")
st.subheader("📽️ Animated District-wise Trend (Simulated Data)")

all_districts = sorted(gdf_districts_full[district_col].dropna().unique().tolist())

# Sidebar dropdown to select a district
selected_district = st.sidebar.selectbox("🎯 Select a District for Trend Animation", all_districts)

# Simulate historical data (e.g., 2000–2023)
years = np.arange(2000, 2024)
random_values = np.random.uniform(low=50, high=300, size=len(years))

# Create base dataframe
district_trend_df = pd.DataFrame({
    "Year": years,
    "Value": random_values,
    "District": selected_district
})

# Prepare cumulative animation frames
animation_frames = []
for year in years:
    frame_df = district_trend_df[district_trend_df["Year"] <= year].copy()
    frame_df["FrameYear"] = year
    animation_frames.append(frame_df)

animated_district_df = pd.concat(animation_frames, ignore_index=True)

# Axis limits for stable animation
y_min = random_values.min() * 0.95
y_max = random_values.max() * 1.05

# Create animated plot
fig_district_trend = px.line(
    animated_district_df,
    x="Year",
    y="Value",
    animation_frame="FrameYear",
    animation_group="District",
    title=f"Animated Trend for {selected_district} (Simulated, 2000–2023)",
    markers=True,
    labels={"Year": "Year", "Value": "Simulated Value", "FrameYear": "Year"},
    range_y=[y_min, y_max],
    range_x=[years.min(), years.max()]
)

# Add play/pause buttons
fig_district_trend.update_layout(
    xaxis_title="Year",
    yaxis_title="Simulated Metric",
    font=dict(family="Poppins, sans-serif", size=12),
    title_font_size=18,
    sliders=[{
        'currentvalue': {'prefix': 'Year: '},
        'pad': {'t': 20}
    }],
    updatemenus=[{
        'type': 'buttons',
        'showactive': False,
        'x': 0.05,
        'y': -0.15,
        'buttons': [
            {
                'label': 'Play',
                'method': 'animate',
                'args': [None, {
                    'frame': {'duration': 200, 'redraw': True},
                    'fromcurrent': True,
                    'transition': {'duration': 100}
                }]
            },
            {
                'label': 'Pause',
                'method': 'animate',
                'args': [[None], {
                    'frame': {'duration': 0, 'redraw': False},
                    'mode': 'immediate',
                    'transition': {'duration': 0}
                }]
            }
        ]
    }]
)

st.plotly_chart(fig_district_trend, use_container_width=True)







