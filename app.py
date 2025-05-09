import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(layout="wide")
st.title("📊 Food Category Forecast Dashboard")

# 1️⃣ Category Dropdown
base_path = "Data/Production"
categories = [f.replace("prod_", "").replace("_", " ").title() 
              for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]

selected_category = st.selectbox("Select Food Category", categories)

# 2️⃣ Load CSVs
folder_name = f"prod_{selected_category.lower().replace(' ', '_')}"
folder_path = os.path.join(base_path, folder_name)

def safe_read(file):
    path = os.path.join(folder_path, file)
    return pd.read_csv(path) if os.path.exists(path) else None

historical_df = safe_read("historical_data.csv")
forecast_df = safe_read("forecast_data.csv")
rmse_df = safe_read("model_rmse.csv")
wg_df = safe_read("wg_report.csv")

# 3️⃣ Visualization: Historical + Forecast + WG Report
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

# 4️⃣ RMSE Table
if rmse_df is not None:
    st.subheader("📊 Model Performance (Root Mean Square %age Error)")
    st.dataframe(rmse_df[['Model', 'Percentage Error']])

#LOGEST Growth Rate
from growth_analysis import plot_logest_growth_from_csv

st.subheader("📈 Decade-wise Logest Growth Rate")

category = st.selectbox("Select Category", os.listdir("Data/Production"))
csv_path = f"Data/Production/{category}/historical_data.csv"

if os.path.exists(csv_path):
    fig = plot_logest_growth_from_csv(csv_path, category.replace("prod_", "").capitalize())
    st.pyplot(fig)
else:
    st.warning("Historical data file not found.")

