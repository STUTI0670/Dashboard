import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from growth_analysis import plot_logest_growth_from_csv

# -------------------- Streamlit Page Config --------------------
st.set_page_config(layout="wide", page_title="India Food Dashboard", page_icon="🌾")

# -------------------- Custom CSS Styling --------------------
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
        margin: 2rem 0 1.5rem;
    }

    .toggle-button {
        font-size: 2.2rem;
        padding: 1.2rem 3rem;
        border-radius: 20px;
        border: 3px solid #333;
        background-color: white;
        cursor: pointer;
        color: #000;
        cursor: pointer;
        transition: all 0.3s ease;
        font-weight: 800;
        margin: 1rem 2rem;
        text-transform: uppercase;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.1);
    }

    .toggle-button:hover {
        transform: scale(1.5);
        background-color: #f0f0f0;
    }

    .toggle-button.selected {
        background-color: black !important;
        color: white !important;
        border: 3px solid #333 !important;
        font-size: 1.6rem;
        transform: scale(2);
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

# -------------------- Session State --------------------
if "selected_type" not in st.session_state:
    st.session_state.selected_type = None

# -------------------- Toggle Buttons --------------------
st.markdown('<div class="toggle-container">', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Production", key="prod"):
        st.session_state.selected_type = "Production"
with col2:
    if st.button("Yield", key="yield"):
        st.session_state.selected_type = "Yield"

st.markdown('</div>', unsafe_allow_html=True)

selected_type = st.session_state.selected_type

if not selected_type:
    st.markdown("<h4 style='text-align:center;'>Please select <b>Production</b> or <b>Yield</b> to continue.</h4>", unsafe_allow_html=True)
    st.stop()

# -------------------- Header --------------------
st.markdown(f"<h1 style='text-align:center;'>🌾 India Food Data Dashboard</h1>", unsafe_allow_html=True)

# -------------------- Folder Setup --------------------
base_path = f"Data/{selected_type}"
prefix = "prod_" if selected_type == "Production" else "yield_"

categories = [
    f.replace(prefix, "").replace("_", " ").title()
    for f in os.listdir(base_path)
    if os.path.isdir(os.path.join(base_path, f))
]

# -------------------- Sidebar --------------------
with st.sidebar:
    st.markdown(f"<div class='sidebar-title'>{selected_type} Categories</div>", unsafe_allow_html=True)
    selected_category = st.radio("Select Category", categories, label_visibility="collapsed")

folder_name = f"{prefix}{selected_category.lower().replace(' ', '_')}"
folder_path = os.path.join(base_path, folder_name)

def safe_read(file_name):
    path = os.path.join(folder_path, file_name)
    return pd.read_csv(path) if os.path.exists(path) else None

# -------------------- Load Files --------------------
historical_df = safe_read("historical_data.csv")
forecast_df = safe_read("forecast_data.csv")
rmse_df = safe_read("model_rmse.csv")
wg_df = safe_read("wg_report.csv")

# -------------------- LOGEST Graph --------------------
st.subheader("📈 Decade-wise Trend Growth Rate")
csv_path = os.path.join(folder_path, "historical_data.csv")
if os.path.exists(csv_path):
    fig = plot_logest_growth_from_csv(csv_path, selected_category)
    st.pyplot(fig)

# -------------------- Forecast Chart --------------------
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

# -------------------- RMSE Table --------------------
if rmse_df is not None:
    st.subheader("📊 Model Performance (% Error)")
    st.dataframe(rmse_df[['Model', 'Percentage Error']])

# -------------------- Placeholder India Map --------------------
st.subheader("🗺️ Interactive India Map (Coming Soon)")
fig = go.Figure(go.Choroplethmapbox(
    geojson="https://raw.githubusercontent.com/plotly/datasets/master/india_states.geojson",
    locations=[], z=[],
    colorscale="Viridis", marker_opacity=0.5, marker_line_width=0
))
fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_zoom=3.5,
    mapbox_center={"lat": 22.9734, "lon": 78.6569},
    margin={"r":0, "t":0, "l":0, "b":0},
    height=500
)
st.plotly_chart(fig, use_container_width=True)
