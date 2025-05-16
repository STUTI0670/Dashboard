import pandas as pd
import plotly.express as px

def plot_forecast_timeline(historical_df, forecast_df, wg_df, unit=""):
    best_models = ["SARIMA", "Auto ARIMA", "Exponential Smoothing"]
    timeline_years = list(range(historical_df["Year"].min(), 2048))

    historical_long = historical_df.rename(columns={"Total": "Value"}).copy()
    historical_long["Model"] = "Historical"

    forecast_long = forecast_df.melt(id_vars="Year", var_name="Model", value_name="Value")
    forecast_long = forecast_long[forecast_long["Model"].isin(best_models)].copy()

    wg_long = wg_df.rename(columns={"Value": "Value", "Scenario": "Model"})[["Year", "Model", "Value"]].copy()
    wg_long["Model"] = "WG Report: " + wg_long["Model"]

    timeline_frames = []
    for frame_year in timeline_years:
        frame_data = []

        hist_copy = historical_long.copy()
        hist_copy["FrameYear"] = frame_year
        frame_data.append(hist_copy)

        forecast_partial = forecast_long[forecast_long["Year"] <= frame_year].copy()
        forecast_partial["FrameYear"] = frame_year
        frame_data.append(forecast_partial)

        wg_partial = wg_long[wg_long["Year"] <= frame_year].copy()
        wg_partial["FrameYear"] = frame_year
        frame_data.append(wg_partial)

        timeline_frames.append(pd.concat(frame_data))

    final_df = pd.concat(timeline_frames)

    y_min = final_df["Value"].min() * 0.95
    y_max = final_df["Value"].max() * 1.05
    x_min = final_df["Year"].min()
    x_max = 2047

    fig = px.line(
        final_df,
        x="Year",
        y="Value",
        color="Model",
        animation_frame="FrameYear",
        title=f"📽️ Forecast Scale: Animated Timeline ({unit})",
        markers=True,
        range_y=[y_min, y_max],
        range_x=[x_min, x_max]
    )

    fig.update_layout(
        yaxis_title=f"Forecast Value ({unit})",
        xaxis_title="Year",
        legend_title="Model"
    )

    return fig
