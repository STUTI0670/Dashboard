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

# ---------- CATEGORY HIERARCHY DEFINITION ----------
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

# ---------- SIDEBAR CONTROLS: CATEGORY HIERARCHY ----------
with st.sidebar:
    st.markdown("### 📂 Select Category")
    level1 = st.selectbox("Category", list(category_hierarchy.keys()))
    level2 = st.selectbox("Subcategory", list(category_hierarchy[level1].keys()))
    level3 = st.selectbox("Group", list(category_hierarchy[level1][level2].keys()))
    level4 = st.selectbox("Item", category_hierarchy[level1][level2][level3])

    # Only Pulses has data; others show error and stop
    if level4 != "Pulses":
        st.error("Data not available for the selected item.")
        st.stop()


# ---------- DYNAMIC LINKS SETUP ----------
# Define your hardcoded URLs for each scenario:
dynamic_links = {
    # Arhar (Kharif)
    ('pulses', 'Kharif', 'Arhar', 'Area'): "https://sprightly-bunny-22a0be.netlify.app/arhar_kharif_area.html",
    ('pulses', 'Kharif', 'Arhar', 'Production'): "https://sprightly-bunny-22a0be.netlify.app/arhar_kharif_production.html",
    ('pulses', 'Kharif', 'Arhar', 'Yield'): "https://sprightly-bunny-22a0be.netlify.app/arhar_kharif_yield.html",

    # Gram (Rabi)
    ('pulses', 'Rabi', 'Gram', 'Area'): "https://fascinating-fenglisu-5e6117.netlify.app/gram_rabi_area.html",
    ('pulses', 'Rabi', 'Gram', 'Production'): "https://fascinating-fenglisu-5e6117.netlify.app/gram_rabi_production.html",
    ('pulses', 'Rabi', 'Gram', 'Yield'): "https://fascinating-fenglisu-5e6117.netlify.app/gram_rabi_yield.html",

    # Khesari (Rabi)
    ('pulses', 'Rabi', 'Khesari', 'Area'): "https://friendly-gecko-bfeb51.netlify.app/khesari_rabi_area.html",
    ('pulses', 'Rabi', 'Khesari', 'Production'): "https://friendly-gecko-bfeb51.netlify.app/khesari_rabi_production.html",
    ('pulses', 'Rabi', 'Khesari', 'Yield'): "https://friendly-gecko-bfeb51.netlify.app/khesari_rabi_yield.html",

    # Kulthi (Kharif, Rabi, Total)
    ('pulses', 'Kharif', 'Kulthi', 'Area'): "https://cozy-ganache-3d493a.netlify.app/kulthi_kharif_area.html",
    ('pulses', 'Kharif', 'Kulthi', 'Production'): "https://cozy-ganache-3d493a.netlify.app/kulthi_kharif_production.html",
    ('pulses', 'Kharif', 'Kulthi', 'Yield'): "https://cozy-ganache-3d493a.netlify.app/kulthi_kharif_yield.html",
    ('pulses', 'Rabi', 'Kulthi', 'Area'): "https://cozy-ganache-3d493a.netlify.app/kulthi_rabi_area.html",
    ('pulses', 'Rabi', 'Kulthi', 'Production'): "https://cozy-ganache-3d493a.netlify.app/kulthi_rabi_production.html",
    ('pulses', 'Rabi', 'Kulthi', 'Yield'): "https://cozy-ganache-3d493a.netlify.app/kulthi_rabi_yield.html",
    ('pulses', 'Total', 'Kulthi', 'Area'): "https://cozy-ganache-3d493a.netlify.app/kulthi_total_area.html",
    ('pulses', 'Total', 'Kulthi', 'Production'): "https://cozy-ganache-3d493a.netlify.app/kulthi_total_production.html",
    ('pulses', 'Total', 'Kulthi', 'Yield'): "https://cozy-ganache-3d493a.netlify.app/kulthi_total_yield.html",

    # Moong (Kharif, Rabi, Total)
    ('pulses', 'Kharif', 'Moong', 'Area'): "https://dynamic-brioche-b7ca0b.netlify.app/moong_kharif_area.html",
    ('pulses', 'Kharif', 'Moong', 'Production'): "https://dynamic-brioche-b7ca0b.netlify.app/moong_kharif_production.html",
    ('pulses', 'Kharif', 'Moong', 'Yield'): "https://dynamic-brioche-b7ca0b.netlify.app/moong_kharif_yield.html",
    ('pulses', 'Rabi', 'Moong', 'Area'): "https://dynamic-brioche-b7ca0b.netlify.app/moong_rabi_area.html",
    ('pulses', 'Rabi', 'Moong', 'Production'): "https://dynamic-brioche-b7ca0b.netlify.app/moong_rabi_production.html",
    ('pulses', 'Rabi', 'Moong', 'Yield'): "https://dynamic-brioche-b7ca0b.netlify.app/moong_rabi_yield.html",
    ('pulses', 'Total', 'Moong', 'Area'): "https://dynamic-brioche-b7ca0b.netlify.app/moong_total_area.html",
    ('pulses', 'Total', 'Moong', 'Production'): "https://dynamic-brioche-b7ca0b.netlify.app/moong_total_production.html",
    ('pulses', 'Total', 'Moong', 'Yield'): "https://dynamic-brioche-b7ca0b.netlify.app/moong_total_yield.html",

    # Moth (Kharif)
    ('pulses', 'Kharif', 'Moth', 'Area'): "https://celebrated-hotteok-b26714.netlify.app/moth_kharif_area.html",
    ('pulses', 'Kharif', 'Moth', 'Production'): "https://celebrated-hotteok-b26714.netlify.app/moth_kharif_production.html",
    ('pulses', 'Kharif', 'Moth', 'Yield'): "https://celebrated-hotteok-b26714.netlify.app/moth_kharif_yield.html",

    # Urad (Kharif, Rabi, Total)
    ('pulses', 'Kharif', 'Urad', 'Area'): "https://resilient-licorice-ca28b9.netlify.app/urad_kharif_area.html",
    ('pulses', 'Kharif', 'Urad', 'Production'): "https://resilient-licorice-ca28b9.netlify.app/urad_kharif_production.html",
    ('pulses', 'Kharif', 'Urad', 'Yield'): "https://resilient-licorice-ca28b9.netlify.app/urad_kharif_yield.html",
    ('pulses', 'Rabi', 'Urad', 'Area'): "https://resilient-licorice-ca28b9.netlify.app/urad_rabi_area.html",
    ('pulses', 'Rabi', 'Urad', 'Production'): "https://resilient-licorice-ca28b9.netlify.app/urad_rabi_production.html",
    ('pulses', 'Rabi', 'Urad', 'Yield'): "https://resilient-licorice-ca28b9.netlify.app/urad_rabi_yield.html",
    ('pulses', 'Total', 'Urad', 'Area'): "https://resilient-licorice-ca28b9.netlify.app/urad_total_area.html",
    ('pulses', 'Total', 'Urad', 'Production'): "https://resilient-licorice-ca28b9.netlify.app/urad_total_production.html",
    ('pulses', 'Total', 'Urad', 'Yield'): "https://resilient-licorice-ca28b9.netlify.app/urad_total_yield.html",

    # Masoor (Rabi)
    ('pulses', 'Rabi', 'Masoor', 'Area'): "https://zingy-custard-fe316d.netlify.app/masoor_rabi_area.html",
    ('pulses', 'Rabi', 'Masoor', 'Production'): "https://zingy-custard-fe316d.netlify.app/masoor_rabi_production.html",
    ('pulses', 'Rabi', 'Masoor', 'Yield'): "https://zingy-custard-fe316d.netlify.app/masoor_rabi_yield.html",

    # Peas (Rabi)
    ('pulses', 'Rabi', 'Peas', 'Area'): "https://tangerine-gingersnap-27e07c.netlify.app/peas_rabi_area.html",
    ('pulses', 'Rabi', 'Peas', 'Production'): "https://tangerine-gingersnap-27e07c.netlify.app/peas_rabi_production.html",
    ('pulses', 'Rabi', 'Peas', 'Yield'): "https://tangerine-gingersnap-27e07c.netlify.app/peas_rabi_yield.html",
}


# Utility to fetch link or fallback
def get_dynamic_link(key_tuple):
    return dynamic_links.get(key_tuple, None)

# ---------- INDIA PULSES CHOROPLETH MAP ----------
st.subheader("🇮🇳 India Pulses Choropleth Map Over Time")


with st.sidebar:
    st.markdown("### 🌱 Pulses Map Settings")
    season = st.selectbox("Select Season", ["Kharif", "Rabi", "Total"])

    # Determine pulses with data for the selected season

    if season != "Total":
        available_pulses = sorted({
            key[2]
            for key in dynamic_links.keys()
            if key[1] == season
        })
    else:
        # Include pulses that have Kharif or Rabi data even if Total is missing
        available_pulses = sorted({
            key[2]
            for key in dynamic_links.keys()
            if key[1] in ["Kharif", "Rabi"]
        })


    
    if not available_pulses:
        st.error(f"No pulses data available for season '{season}'.")
        st.stop()

    pulse_type = st.selectbox("Select Pulse Type", available_pulses)

    metric = st.selectbox("Select Metric", ["Area", "Production", "Yield"])

    # Insert Dynamic view link for pulses map
    dyn_key = ('pulses', season, pulse_type, metric)
    dyn_url = get_dynamic_link(dyn_key)
    if dyn_url:
        st.markdown(f"[🔗 Dynamic view]({dyn_url})", unsafe_allow_html=True)


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
    #df = df[df["Season"].str.lower() == season.lower()]
    # Normalize column formatting
    df["Season"] = df["Season"].str.strip().str.lower()
    df["Year"] = df["Year"].astype(str)
    df["State"] = df["State"].str.strip()
    df[metric] = pd.to_numeric(df[metric], errors="coerce")

    # Handle 'Total' season logic
    if season.lower() == "total":
        # Check if 'total' data exists
        total_df = df[df["Season"] == "total"]
    
        if total_df.empty:
            # If no direct total data, compute from Kharif + Rabi
            kharif_df = df[df["Season"] == "kharif"]
            rabi_df = df[df["Season"] == "rabi"]

            # Combine both
            combined_df = pd.concat([kharif_df, rabi_df])

            # Group by State and Year and aggregate
            df = combined_df.groupby(["State", "Year"], as_index=False)[metric].sum()
            df["Season"] = "total"
        else:
            df = total_df
    else:
        # Filter season-wise normally
        df = df[df["Season"] == season.lower()]



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
        "Andaman & Nicobar Islands": "Andaman & Nicobar",
        "INDIA": None
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
    fig, ax = plt.subplots(1, 1, figsize=(6, 4))
    merged.plot(
        column=metric,
        ax=ax,
        legend=True,
        cmap='YlOrRd',
        
        missing_kwds={"color": "white", "edgecolor": "gray"}
    )
    ax.set_title(f"{pulse_type} - {season} - {metric} in {selected_year}", fontsize=12)
    st.pyplot(fig)


except Exception as e:
    st.error(f"An error occurred: {e}")

# gdf-districts code

# Load full India District shapefile (load once → top of file / cache)
@st.cache_data
def load_india_districts_shapefile():
    gdf = gpd.read_file("India_Shapefile/State/2011_Dist.shp")
    gdf = gdf.set_crs(epsg=4326, inplace=False)
    return gdf



State_Name_CORRECTIONS = {
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
gdf_districts["ST_NM"] = gdf_districts["ST_NM"].replace(State_Name_CORRECTIONS)
gdf_districts["ST_NM"] = gdf_districts["ST_NM"].str.strip().str.upper()

# ---------- FULL INDIA DISTRICT MAP ----------
st.markdown("---")
st.subheader("🇮🇳 Full India District Map View (Fabricated Values)")

# Insert Dynamic view link for full district map
dyn_key_full = ('full', season, pulse_type, metric)
dyn_url_full = get_dynamic_link(dyn_key_full)
if dyn_url_full:
    st.markdown(f"[🔗 Dynamic view]({dyn_url_full})")

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
    for State_Name in df_selected_year["State"].unique():
        State_Name_upper = State_Name.strip().upper()

        # Match in shapefile with normalization
        def normalize_State_Name(s):
            return s.upper().replace(" ", "")

        mask = gdf_districts_full[state_col].apply(normalize_State_Name) == normalize_State_Name(State_Name_upper)
        state_gdf = gdf_districts_full[mask]

        # If no matching districts → skip
        if state_gdf.empty:
            continue

        # Get state total value from df_selected_year
        state_row = df_selected_year[df_selected_year["State"].str.upper() == State_Name_upper]
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
    fig_full, ax_full = plt.subplots(1, 1, figsize=(6, 4))
    gdf_districts_full.plot(
        column="Dummy_Value",
        ax=ax_full,
        legend=True,
        cmap='YlOrRd',
        edgecolor='gray',
        missing_kwds={"color": "white", "edgecolor": "gray"}
    )
    ax_full.set_title(f"Full India District Map - {metric} ({season}, {pulse_type}, {selected_year})", fontsize=16)

    st.pyplot(fig_full)



# ---------- STATE MAP VIEW ----------


# Sidebar: State Map View
st.sidebar.markdown("---")
st.sidebar.markdown("### 🗺️ State Map View")

# Dynamic State Map View dropdown

# Extract available states in current df_selected_year
available_states = df_selected_year["State"].str.upper().unique().tolist()

# Remove "INDIA" from the list
available_states = [s for s in available_states if s != "INDIA"]

# Dropdown options → dynamic + "None" on top
state_options = ["None"] + sorted(available_states)

selected_state_map = st.sidebar.selectbox("Select State for State Map", state_options)

#   After subheader for state map
if selected_state_map != "None":
    #st.markdown(f"### 📍 {selected_state_map} District Map - {metric} ({season}, {pulse_type})")
    # Insert Dynamic view link for state-level map
    dyn_key_state = ('state', season, pulse_type, metric)
    dyn_url_state = get_dynamic_link(dyn_key_state)
    if dyn_url_state:
        st.markdown(f"[🔗 Dynamic view]({dyn_url_state})")


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
        def normalize_State_Name(s):
            return s.upper().replace(" ", "")

        # Filter for selected state safely
        state_gdf = gdf_districts[gdf_districts[state_col].apply(normalize_State_Name) == normalize_State_Name(selected_state_map)]


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

            fig2, ax2 = plt.subplots(1, 1, figsize=(6, 4))
            state_gdf.plot(
                column="Dummy_Value",
                ax=ax2,
                legend=True,
                cmap='YlOrRd',
                edgecolor='gray',
                missing_kwds={"color": "white", "edgecolor": "gray"}
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
                                    'frame': {'duration': 100, 'redraw': True},  # << faster animation (300 ms per frame)
                                    'fromcurrent': True,
                                    'transition': {'duration': 0}
                                }]
                            }, {
                            'label': 'Pause',
                            'method': 'animate',
                            'args': [[None], {
                                'frame': {'duration': 50, 'redraw': False},
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



# ---------- DISTRICT-WISE ANIMATED HISTORICAL PLOT (RANDOM VALUES) ----------
st.markdown("---")
st.subheader("📽️ Animated District-wise Trend (Simulated Data)")

# Filter districts for the selected state
if selected_state_map != "None":
    filtered_districts = gdf_districts_full[
        gdf_districts_full[state_col].str.upper() == selected_state_map.upper()
    ][district_col].dropna().unique().tolist()
    filtered_districts = sorted(filtered_districts)
else:
    filtered_districts = []

# Dropdown to select district (only from that state)
if filtered_districts:
    selected_district = st.sidebar.selectbox("🎯 Select a District for Trend Animation", filtered_districts)
else:
    selected_district = None
    st.sidebar.warning("No districts available for selected state.")

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
                    'transition': {'duration': 0}
                }]
            },
            {
                'label': 'Pause',
                'method': 'animate',
                'args': [[None], {
                    'frame': {'duration': 50, 'redraw': False},
                    'mode': 'immediate',
                    'transition': {'duration': 0}
                }]
            }
        ]
    }]
)

st.plotly_chart(fig_district_trend, use_container_width=True)

def show_india_timelapse_map(df, geojson_path, metric_title="Production", default_unit="Tonnes"):
    # Load GeoJSON file
    with open(geojson_path, "r") as f:
        india_states_geojson = json.load(f)

    # Determine unit
    unit = df["Unit"].iloc[0] if "Unit" in df.columns and not df["Unit"].isna().all() else default_unit
    title = f"{metric_title} Over Time ({unit})"

    # Create choropleth
    fig = px.choropleth(
        df,
        geojson=india_states_geojson,
        locations="State",                        # Your CSV column name
        featureidkey="properties.State_Name",         # Your GeoJSON property
        color="Value",
        hover_name="State",
        animation_frame="Year",
        color_continuous_scale="YlGnBu",
        title=title
    )

    # Layout tweaks
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        coloraxis_colorbar=dict(title=unit),
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        updatemenus=[{
            "type": "buttons",
            "buttons": [ 
                {
                    "label": "Play",
                    "method": "animate",
                    "args": [None, {
                        "frame": {"duration": 50, "redraw": True},
                        "fromcurrent": True,
                        "transition": {"duration": 0, "easing": "linear"}
                    }]
                },
                {
                    "label": "Pause",
                    "method": "animate",
                    "args": [[None], {
                        "mode": "immediate",
                        "frame": {"duration": 0},
                        "transition": {"duration": 10}
                    }]
                }
            ]
        }]
    )

    st.plotly_chart(fig, use_container_width=True)


with open("states_india.geojson", "r", encoding="utf-8") as f:
    india_geojson = json.load(f)

