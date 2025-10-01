import streamlit as st
import pandas as pd
from Data_loader import load_data


# Set a large, styled title and subtitle for the table
st.title("Data Table")
st.write("This table summarizes the first month's data for each variable, with sparklines for visualization.")  


# Load the data using the cached loader
df = load_data()

# Filter the DataFrame to only include data from the first month
first_month = df.index.min().to_period("M")
first_month_df = df[df.index.to_period("M") == first_month]

# Create a summary table: one row per variable, with a sparkline for the first month
summary_table = pd.DataFrame({
    "Variable Name": first_month_df.columns,
    "First Month Values": [first_month_df[col].tolist() for col in first_month_df.columns],
})

# Display the summary table with sparklines for each variable
st.dataframe(
    summary_table,
    hide_index=True,
    use_container_width=True,
    column_config={
        "First Month Values": st.column_config.LineChartColumn(
        "First Month Values", width="large"
        )
    },
)