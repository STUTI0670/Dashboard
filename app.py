import streamlit as st
import pandas as pd
import os
import plotly.express as px
from growth_analysis import plot_logest_growth_from_csv
import plotly.graph_objects as go

# Streamlit Config
st.set_page_config(layout="wide")
st.title("🌾 India Food Data Dashboard")

# Inject Custom CSS for Toggle Styling
st.markdown("""
    <style>
    .option-container {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin-bottom: 2rem;
    }
    .option-button {
        font-size: 24px;
        padding: 0.6rem 1.8rem;
        border-radius: 10px;
        background-color: #1f1f1f;
        border: 2px solid #333;
        color: #fff;
        cursor: pointer;
        transition: all 0.3s ease-in-out;
    }
    .option-button:hover {
        transform: scale(1.05);
        background-color: #333;
    }
    .selected {
        background-color: #14b8a6 !important;
        border: 2px solid #0f766e !important;
        font-weight: bold;
        transform: scale(1.1);
    }
    </style>
""", unsafe_allow_html=True)

# Session State Initialization
if "selected_type" not in st.session_state:
    st.session_state.selected_type = None

# Toggle Buttons (Production/Yield)
st.markdown('<div class="option-container">', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    if st.button("Production"):
        st.session_state.selected_type = "Production"

with col2:
    if st.button("Yield"):
        st.session_state.selected_type = "Yield"
st.markdown('</div>', unsafe_allow_html=True)

# Store selected data type
data_type = st.session_state.selected_type

# If nothing selected, stop execution
if data_type is None:
    st.warning("Please select a data type to proceed.")
    st.stop()

# Show selection
st.markdown(f"<h4 style='text-align:center;'>You selected <b>{data_type}</b></h4>", unsafe_allow_html=True)

# Path Setup
base_path = f"Data/{data_type}"
prefix = "prod" if data_type == "Production" else "yield"

# List categories
categories = [f.replace(f"{prefix}_", "").replace("_", " ").title()
              for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]

# Sidebar for Category Selection
with st.sidebar:
    st.markdown(f"### {data_type} Categories")
    selected_category = st.radio("Select Category", categories)

# Get folder path
folder_name = f"{prefix}_{selected_category.lower().replace(' ', '_')}"
folder_path = os.path.join(base_path, folder_name)

# Read CSV safely
def safe_read(file):
    path = os.path.join(folder_path, file)
    return pd.read_csv(path) if os.path.exists(path) else None

historical_df = safe_read("historical_data.csv")
forecast_df = safe_read("forecast_data.csv")
rmse_df = safe_read("model_rmse.csv")
wg_df = safe_read("wg_report.csv")

# 📈 Decade-wise Logest Growth
st.subheader("📈 Decade-wise Trend Growth Rate")
csv_path = os.path.join(folder_path, "historical_data.csv")
if os.path.exists(csv_path):
    fig = plot_logest_growth_from_csv(csv_path, selected_category)
    st.pyplot(fig)

# 🔮 Forecast Chart
if historical_df is not None and forecast_df is not None:
    st.subheader("🔮 Historical and Predicted Forecasts")
    fig = px.line()
    fig.add_scatter(x=historical_df["Year"], y=historical_df["Total"], mode="lines+markers", name="Historical", line=dict(color="black"))

    for col in forecast_df.columns[1:]:
        fig.add_scatter(x=forecast_df["Year"], y=forecast_df[col], mode="lines+markers", name=col)

    if wg_df is not None:
        fig.add_scatter(x=wg_df["Year"], y=wg_df["Value"], mode="markers+text", name="WG Report",
                        marker=dict(color="red", size=10),
                        text=wg_df["Scenario"], textposition="top right")

    st.plotly_chart(fig, use_container_width=True)

# 📊 RMSE Table
if rmse_df is not None:
    st.subheader("📊 Model Performance (% Error)")
    st.dataframe(rmse_df[['Model', 'Percentage Error']])

# 🗺️ Placeholder for Interactive India Map
st.subheader("🗺️ Placeholder for Interactive Heatmap")
fig = go.Figure(go.Choroplethmapbox(
    geojson="https://raw.githubusercontent.com/plotly/datasets/master/india_states.geojson",
    locations=[],
    z=[],
    colorscale="Viridis",
    marker_opacity=0.5,
    marker_line_width=0
))
fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_zoom=3.5,
    mapbox_center={"lat": 22.9734, "lon": 78.6569},
    margin={"r":0, "t":0, "l":0, "b":0},
    height=500
)
st.plotly_chart(fig)
