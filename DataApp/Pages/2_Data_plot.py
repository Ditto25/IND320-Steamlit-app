import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from Data_loader import load_data

st.title("Plot Explorer")
st.write("Use the controls below to explore the data by column and month.")

# Load data
df = load_data()  # DataFrame with time index

# ---- Controls ----
options = ["All columns"] + list(df.columns)
choice = st.selectbox("Select column to plot", options, index=0)

months = sorted(df.index.to_period("M").unique())
labels = [str(m) for m in months]

start_label, end_label = st.select_slider(
    "Select month range",
    options=labels,
    value=(labels[0], labels[0])  # default = first month
)

# ---- Subset by month range ----
start_p = pd.Period(start_label, freq="M")
end_p   = pd.Period(end_label,   freq="M")
mask = (df.index.to_period("M") >= start_p) & (df.index.to_period("M") <= end_p)
d = df.loc[mask]

# ---- Plot ----
fig, ax = plt.subplots(figsize=(10, 4))
if choice == "All columns":
    d.plot(ax=ax)
    ax.set_title("All Columns Over Time")
    ax.set_ylabel("Value")
else:
    d[choice].plot(ax=ax)
    ax.set_title(f"{choice} Over Time")
    ax.set_ylabel(choice)

ax.set_xlabel("Time")
ax.grid(True)
plt.tight_layout()
st.pyplot(fig)