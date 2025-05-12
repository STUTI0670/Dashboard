import streamlit as st
import pandas as pd
import os
import plotly.express as px
from growth_analysis import plot_logest_growth_from_csv
import plotly.graph_objects as go

# Set wide layout early
st.set_page_config(layout="wide")

# Load custom CSS
with open("dashboard_style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Custom toggle button logic
if "selected_type" not in st.session_state:
    st.session_state.selected_type = None

st.markdown("""
<div class="toggle-container">
    <div class="toggle-header">
        <span class='toggle-option {prod_class}' onclick="window.location.href='/?selected_type=Production'">Production</span>
        <span class='toggle-option {yield_class}' onclick="window.location.href='/?selected_type=Yield'">Yield</span>
    </div>
</div>
""".format(
    prod_class="selected" if st.session_state.selected_type == "Production" else "",
    yield_class="selected" if st.session_state.selected_type == "Yield" else ""
), unsafe_allow_html=True)

# Update selected_type via query parameter
query_params = st.experimental_get_query_params()
if "selected_type" in query_params:
    st.session_state.selected_type = query_params["selected_type"][0]

selected_type = st.session_state.selected_type

if not selected_type:
    st.warning("Please select either **Production** or **Yield** to begin.")
    st.stop()

# Sidebar category ribbon
st.sidebar.title(f"{selected_type} Categories")
base_path = f"Data/{selected_type}"
categories = [f.replace("prod_", "").replace("_", " ").title()
              for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]

selected_category = st.sidebar.radio("Select Category", categories)

# Construct path for selected category
folder_name = f"prod_{selected_category.lower().replace(' ', '_')}"
folder_path = os.path.join(base_path, folder_name)

# Helper to safely load CSVs
def safe_read(file):
    path = os.path.join(folder_path, file)
    return pd.read_csv(path) if os.path.exists(path) else None

# Load data files
historical_df = safe_read("historical_data.csv")
forecast_df = safe_read("forecast_data.csv")
rmse_df = safe_read("model_rmse.csv")
wg_df = safe_read("wg_report.csv")

# 1️⃣ Logest Growth Chart
st.subheader("📈 Decade-wise Trend Growth Rate")
csv_path = os.path.join(folder_path, "historical_data.csv")
if os.path.exists(csv_path):
    fig = plot_logest_growth_from_csv(csv_path, selected_category)
    st.pyplot(fig)

# 2️⃣ Forecast Plot
if historical_df is not None and forecast_df is not None:
    st.subheader("🔮 Historical and Predicted Forecasts")

    fig = px.line()
    fig.add_scatter(x=historical_df["Year"], y=historical_df["Total"],
                    mode="lines+markers", name="Historical", line=dict(color="black"))

    for col in forecast_df.columns[1:]:
        fig.add_scatter(x=forecast_df["Year"], y=forecast_df[col],
                        mode="lines+markers", name=col)

    if wg_df is not None:
        fig.add_scatter(x=wg_df["Year"], y=wg_df["Value"],
                        mode="markers+text", name="WG Report",
                        marker=dict(color="red", size=10),
                        text=wg_df["Scenario"], textposition="top right")

    st.plotly_chart(fig, use_container_width=True)

# 3️⃣ RMSE Table
if rmse_df is not None:
    st.subheader("📊 Model Performance (% Error)")
    st.dataframe(rmse_df[['Model', 'Percentage Error']])

# 4️⃣ Placeholder for Interactive Map
st.subheader("🗺️ Placeholder: India Map for Heatmap")

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

st.plotly_chart(fig, use_container_width=True)
