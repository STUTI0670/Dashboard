import streamlit as st
import pandas as pd
import os
import plotly.express as px
from growth_analysis import plot_logest_growth_from_csv
import plotly.graph_objects as go

# ---------------------- Inject Modern CSS & JS ----------------------
st.markdown("""
    <style>
        body {
            font-family: 'Poppins', sans-serif;
        }
        .center-container {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 3rem;
            margin-top: 2rem;
        }
        .toggle-btn {
            padding: 0.8rem 2.5rem;
            border-radius: 12px;
            background-color: #f1f3f6;
            color: #1f2937;
            font-weight: 600;
            font-size: 1.2rem;
            border: none;
            cursor: pointer;
            transition: all 0.4s ease-in-out;
            box-shadow: 0px 4px 12px rgba(0,0,0,0.1);
        }
        .toggle-btn:hover {
            transform: scale(1.07);
            background-color: #e5e7eb;
        }
        .toggle-selected {
            background-color: #4f46e5 !important;
            color: white !important;
            transform: scale(1.15);
            font-size: 1.4rem;
        }
        .category-ribbon {
            background-color: #f9fafb;
            padding: 1.5rem;
            border-radius: 10px;
            margin-top: 2rem;
            box-shadow: 0px 2px 10px rgba(0,0,0,0.05);
        }
        .category-title {
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 0.8rem;
            color: #374151;
        }
    </style>
    <script>
        function setSelected(btnId) {
            const buttons = document.querySelectorAll('.toggle-btn');
            buttons.forEach(btn => btn.classList.remove('toggle-selected'));
            const selected = document.getElementById(btnId);
            selected.classList.add('toggle-selected');
        }
    </script>
""", unsafe_allow_html=True)

# ---------------------- Session State Init ----------------------
if "selected_type" not in st.session_state:
    st.session_state.selected_type = ""

# ---------------------- Title ----------------------
st.markdown("<h1 style='text-align:center; font-size: 2.8rem; margin-top:1rem;'>🌾 India Food Data Dashboard</h1>", unsafe_allow_html=True)

# ---------------------- Selection UI ----------------------
st.markdown('<div class="center-container">', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Production", key="production"):
        st.session_state.selected_type = "Production"
with col2:
    if st.button("Yield", key="yield"):
        st.session_state.selected_type = "Yield"

st.markdown('</div>', unsafe_allow_html=True)

st.markdown(f"""
    <script>
        setTimeout(function() {{
            setSelected('{st.session_state.selected_type.lower()}');
        }}, 10);
    </script>
""", unsafe_allow_html=True)

# ---------------------- Block If Not Selected ----------------------
if not st.session_state.selected_type:
    st.markdown("<h4 style='text-align:center;'>Please select <b>Production</b> or <b>Yield</b> to continue.</h4>", unsafe_allow_html=True)
    st.stop()

data_type = st.session_state.selected_type
base_path = f"Data/{data_type}"

# ---------------------- Get Categories ----------------------
categories = [f.replace("prod_", "").replace("_", " ").title()
              for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]

with st.sidebar:
    st.markdown(f"<div class='category-ribbon'><div class='category-title'>{data_type} Categories</div>", unsafe_allow_html=True)
    selected_category = st.radio("Select Category", categories, label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------- Load Data ----------------------
folder_name = f"prod_{selected_category.lower().replace(' ', '_')}"
folder_path = os.path.join(base_path, folder_name)

def safe_read(file):
    path = os.path.join(folder_path, file)
    return pd.read_csv(path) if os.path.exists(path) else None

historical_df = safe_read("historical_data.csv")
forecast_df = safe_read("forecast_data.csv")
rmse_df = safe_read("model_rmse.csv")
wg_df = safe_read("wg_report.csv")

# ---------------------- Growth Plot ----------------------
st.subheader("📈 Decade-wise Trend Growth Rate")
csv_path = os.path.join(folder_path, "historical_data.csv")
if os.path.exists(csv_path):
    fig = plot_logest_growth_from_csv(csv_path, selected_category)
    st.pyplot(fig)

# ---------------------- Forecast Chart ----------------------
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

# ---------------------- RMSE Table ----------------------
if rmse_df is not None:
    st.subheader("📊 Model Performance (% Error)")
    st.dataframe(rmse_df[['Model', 'Percentage Error']])

# ---------------------- Heatmap Placeholder ----------------------
st.subheader("🗺️ Interactive India Map (Coming Soon)")
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
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    height=500
)
st.plotly_chart(fig)
