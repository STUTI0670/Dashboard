import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from growth_analysis import plot_logest_growth_from_csv

st.set_page_config(layout="wide")
st.title("📊 Food Category Forecast Dashboard")

# 1️⃣ Category Dropdown
base_path = "Data/Production"
category_folders = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
display_to_folder = {
    f.replace("prod_", "").replace("_", " ").title(): f
    for f in category_folders
}

selected_category = st.selectbox("Select Food Category", list(display_to_folder.keys()))

# Convert selection to matching folder
folder_name = display_to_folder[selected_category]
folder_path = os.path.join(base_path, folder_name)

# File readers
def safe_read(file):
    path = os.path.join(folder_path, file)
    return pd.read_csv(path) if os.path.exists(path) else None

historical_df = safe_read("historical_data.csv")
forecast_df = safe_read("forecast_data.csv")
rmse_df = safe_read("model_rmse.csv")
wg_df = safe_read("wg_report.csv")

# 2️⃣ LOGEST Growth Rate First
st.subheader("📈 Decade-wise Logest Growth Rate")
csv_path = os.path.join(folder_path, "historical_data.csv")

if os.path.exists(csv_path):
    fig = plot_logest_growth_from_csv(csv_path, selected_category)
    st.pyplot(fig)
else:
    st.warning("Historical data file not found for growth rate chart.")

# 3️⃣ Forecast + WG Visualization
if historical_df is not None and forecast_df is not None:
    st.subheader("📈 Historical and Predicted Trends")

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

# 4️⃣ RMSE Table (Percentage Error Only)
if rmse_df is not None:
    st.subheader("📊 Model Performance (Percentage Error Only)")
    st.dataframe(rmse_df[['Model', 'Percentage Error']])

st.subheader("🗺️ India Map - Area/Production/Yield (Coming Soon)")

# Create empty India map as placeholder
fig = go.Figure(go.Choroplethmapbox(
    geojson="https://raw.githubusercontent.com/plotly/datasets/master/india_states.geojson",
    locations=[],  # No data yet
    z=[],           # No values
    colorscale="Viridis",
    marker_opacity=0.5,
    marker_line_width=0
))

fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_zoom=3.5,
    mapbox_center={"lat": 22.9734, "lon": 78.6569},  # Center of India
    margin={"r":0, "t":0, "l":0, "b":0},
    height=500
)

st.plotly_chart(fig, use_container_width=True)
