import streamlit as st
import plotly.express as px
import pandas as pd

def show_world_timelapse_map(df, metric_title="Production", default_unit="Tonnes"):
    unit = df["Unit"].iloc[0] if "Unit" in df.columns and not df["Unit"].isna().all() else default_unit
    title = f"{metric_title} Over Time ({unit})"

    fig = px.choropleth(
        df,
        locations="Country",
        locationmode="country names",
        color="Value",
        hover_name="Country",
        animation_frame="Year",
        color_continuous_scale="YlGnBu",
        title=title
    )

    fig.update_layout(
        geo=dict(showframe=False, showcoastlines=False),
        coloraxis_colorbar=dict(title=unit),
        margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )

    st.plotly_chart(fig, use_container_width=True)
