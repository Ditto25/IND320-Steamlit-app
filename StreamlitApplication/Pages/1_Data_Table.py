import streamlit as st
import pandas as pd
import numpy as np
from StreamlitApplication.Data_loader import load_data


def pretty_name(col: str) -> str:
    """Convert a column name to a nicer display name (remove underscores, title case)."""
    return col.replace("_", " ").title()


# Page header
st.title("Data Table")
st.write("This table summarizes the first month's data for each variable using compact sparklines.")


# Load data
df = load_data()

# Select first month
first_month = df.index.min().to_period("M")
first_month_df = df[df.index.to_period("M") == first_month]


# Preprocessing defaults (no UI on this page)
smooth = False
standardize = False
unwrap_wind = False


# Make a copy for processing
proc = first_month_df.copy()

# Unwrap wind direction columns if requested
wind_cols = [c for c in proc.columns if "wind_direction" in c.lower()]
if unwrap_wind and wind_cols:
    for wc in wind_cols:
        radians = np.deg2rad(proc[wc].to_numpy())
        proc[wc] = np.rad2deg(np.unwrap(radians))

# Smooth if requested
if smooth:
    proc = proc.rolling(window=5, min_periods=1).mean()

# Standardize if requested
if standardize:
    proc = (proc - proc.mean()) / proc.std(ddof=0)


# Build table for display: pretty variable name + list of first-month values
display_df = pd.DataFrame({
    "Variable": [pretty_name(c) for c in proc.columns],
    "First month": [proc[c].tolist() for c in proc.columns],
})

# Show table with larger sparklines for readability
st.dataframe(
    display_df,
    hide_index=True,
    use_container_width=True,
    column_config={
        "First month": st.column_config.LineChartColumn("First month", width="large")
    },
)


# --- Large plot viewer for a selected variable ---
# made for easier see each table variable in a larger plot

st.subheader("Inspect a Variable From January 2020")
var = st.selectbox("Choose variable", options=list(proc.columns))
if var:
    st.write(f"#### {pretty_name(var)}")
    st.line_chart(proc[var], use_container_width=True, height=360)

