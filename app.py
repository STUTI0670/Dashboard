import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from growth_analysis import plot_logest_growth_from_csv

st.set_page_config(layout="wide", page_title="India Food Dashboard", page_icon="🌾")

# Inject custom CSS for big toggle buttons
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }

    .toggle-container {
        display: flex;
        justify-content: center;
        gap: 3rem;
        margin: 3rem 0;
    }

    .toggle-button {
        font-size: 2.8rem;
        padding: 1.5rem 3.5rem;
        border-radius: 25px;
        border: 3px solid #222;
        background-color: white;
        color: #222;
        cursor: pointer;
        transition: all 0.3s ease-in-out;
        font-weight: 800;
        box-shadow: 0px 6px 16px rgba(0, 0, 0, 0.15);
        text-transform: uppercase;
    }

    .toggle-button:hover {
        background-color: #eee;
        transform: scale(1.08);
    }

    .toggle-button.selected {
        background-color: #111 !important;
        color: white !important;
        transform: scale(1.2);
        border-color: #444;
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

# Session state
if "selected_type" not in st.session_state:
    st.session_state.selected_type = None

# Toggle Buttons
prod_selected = st.session_state.selected_type == "Production"
yield_selected = st.session_state.selected_type == "Yield"

toggle_html = f"""
<div class="toggle-container">
    <form action="" method="post">
        <button type="submit" name="selection" value="Production" class="toggle-button {'selected' if prod_selected else ''}">Production</button>
        <button type="submit" name="selection" value="Yield" class="toggle-button {'selected' if yield_selected else ''}">Yield</button>
    </form>
</div>
"""

selection = st.experimental_get_query_params().get("selection", [None])[0]
if selection:
    st.session_state.selected_type = selection

st.markdown(toggle_html, unsafe_allow_html=True)

if not st.session_state.selected_type:
    st.markdown("<h4 style='text-align:center;'>Please select <b>Production</b> or <b>Yield</b> to continue.</h4>", unsafe_allow_html=True)
    st.stop()

selected_type = st.session_state.selected_type

# Header
st.markdown(f"<h1 style='text-align:center;'>🌾 India Food Data Dashboard</h1>", unsafe_allow_html=True)

# Folder Setup
base_path = f"Data/{selected_type}"
prefix = "prod_" if selected_type == "Production" else "yield_"

categories = [
    f.replace(prefix, "").replace("_", " ").title()
    for f in os.listdir(base_path)
    if os.path.isdir(os.path.join(base_path, f))
]

# Sidebar
with st.sidebar:
    st.markdown(f"<div class='sidebar-title'>{selected_type} Categories</div>", unsafe_allow_html=True)
    selected_category = st.radio("Select Category", categories, label_visibility="collapsed")

folder_name = f"{prefix}{selected_category.lower().replace(' ', '_')}"
folder_path = os.path.join(base_path, folder_name)

def safe_read(file_name):
    path = os.path.join(folder_path, file_name)
    return pd.read_csv(path) if os.path.exists(path) else None

historical_df = safe_read("historical_data.csv")
forecast_df = safe_read("forecast_data.csv")
rmse_df = safe_read("model_rmse.csv")
wg_df = safe_read("wg_report.csv")

# LOGEST Graph
st.subheader("📈 Decade-wise Trend Growth Rate")
csv_path = os.path.join(folder_path, "historical_data.csv")
if os.path.exists(csv_path):
    fig = plot_logest_growth_from_csv(csv_path, selected_category)
    st.pyplot(fig)

# Forecast Chart
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

# RMSE Table
if rmse_df is not None:
    st.subheader("📊 Model Performance (% Error)")
    st.dataframe(rmse_df[['Model', 'Percentage Error']])

# India Map Placeholder
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
