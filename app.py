import streamlit as st
import pandas as pd
import os
import plotly.express as px
from growth_analysis import plot_logest_growth_from_csv

st.set_page_config(layout="wide")
st.title("🌾 India Food Data Dashboard")

# Step 1: Choose between Production or Yield
data_type = st.radio("Choose Data Type", ["Production", "Yield"], horizontal=True)

# Step 2: Get categories based on selection
base_path = f"Data/{data_type}"
categories = [f.replace("prod_", "").replace("_", " ").title()
              for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]

# Step 3: Sidebar Ribbon for category selection
with st.sidebar:
    st.markdown(f"### {data_type} Categories")
    selected_category = st.radio("Select Category", categories)

folder_name = f"prod_{selected_category.lower().replace(' ', '_')}"
folder_path = os.path.join(base_path, folder_name)

# Step 4: Load Data
def safe_read(file): return pd.read_csv(os.path.join(folder_path, file)) if os.path.exists(os.path.join(folder_path, file)) else None

historical_df = safe_read("historical_data.csv")
forecast_df = safe_read("forecast_data.csv")
rmse_df = safe_read("model_rmse.csv")
wg_df = safe_read("wg_report.csv")

# Step 5: LOGEST Growth Chart
st.subheader("📈 Decade-wise Trend Growth Rate")
csv_path = os.path.join(folder_path, "historical_data.csv")
if os.path.exists(csv_path):
    fig = plot_logest_growth_from_csv(csv_path, selected_category)
    st.pyplot(fig)

# Step 6: Forecast Chart
if historical_df is not None and forecast_df is not None:
    st.subheader("🔮 Historical and Predicted Forecasts")

    fig = px.line()
    fig.add_scatter(x=historical_df["Year"], y=historical_df["Total"], mode="lines+markers", name="Historical", line=dict(color="black"))

    for col in forecast_df.columns[1:]:
        fig.add_scatter(x=forecast_df["Year"], y=forecast_df[col], mode="lines+markers", name=col)

    if wg_df is not None:
        fig.add_scatter(x=wg_df["Year"], y=wg_df["Value"], mode="markers+text", name="WG Report", marker=dict(color="red", size=10), text=wg_df["Scenario"], textposition="top right")

    st.plotly_chart(fig, use_container_width=True)

# Step 7: RMSE Table
if rmse_df is not None:
    st.subheader("📊 Model Performance (% Error)")
    st.dataframe(rmse_df[['Model', 'Percentage Error']])


st.subheader("🗺️ Placeholder for Interactive Heatmap")

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
