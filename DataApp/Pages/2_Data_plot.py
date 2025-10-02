
# Import necessary libraries
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from Data_loader import load_data


# Set the page title and description
st.title("Plot Explorer")
st.write("Use the controls below to explore the data by column and month.")


# Load the data using the cached loader
df = load_data()  # DataFrame with time index


# ---- Controls ----
# Dropdown to select a column or all columns
options = ["All columns"] + list(df.columns)
choice = st.selectbox("Select column to plot", options, index=0)

# Slider to select a range of months (defaults to first month)
months = sorted(df.index.to_period("M").unique())
labels = [str(m) for m in months]

start_label, end_label = st.select_slider(
    "Select month range",
    options=labels,
    value=(labels[0], labels[0])  # default = first month
)


# ---- Subset by month range ----
# Filter the DataFrame to only include data within the selected month range
start_p = pd.Period(start_label, freq="M")
end_p   = pd.Period(end_label,   freq="M")
mask = (df.index.to_period("M") >= start_p) & (df.index.to_period("M") <= end_p)
d = df.loc[mask]


# ---- Smoothing and Standardization Option ----
# Option to smooth and standardize the data for better comparison
st.markdown("---")
st.subheader("Plot Options")
smooth = st.checkbox(
    "Smooth and standardize (z-score) all columns (recommended for comparison)", value=False
)

# ---- Plotting ----
fig, ax = plt.subplots(figsize=(10, 4))
if choice == "All columns":
    plot_df = d.copy()
    if smooth:
        # Apply rolling mean (window=5) and z-score standardization to all columns
        plot_df = plot_df.rolling(window=5, min_periods=1).mean()
        plot_df = (plot_df - plot_df.mean()) / plot_df.std(ddof=0)
    plot_df.plot(ax=ax)
    ax.set_title("All Columns Over Time" + (" (Standardized & Smoothed)" if smooth else ""))
    ax.set_ylabel("z-score" if smooth else "Value")
else:
    plot_series = d[choice].copy()
    if smooth:
        # Apply rolling mean (window=5) to the selected column
        plot_series = plot_series.rolling(window=5, min_periods=1).mean()
    plot_series.plot(ax=ax)
    ax.set_title(f"{choice} Over Time" + (" (Smoothed)" if smooth else ""))
    ax.set_ylabel(choice)

# Set x-axis label and grid for clarity
ax.set_xlabel("Time")
ax.grid(True)
plt.tight_layout()

# Display the plot in the Streamlit app
st.pyplot(fig)