import streamlit as st
import pandas as pd
from Data_loader import load_data

st.title("Streamlit App")
st.set_page_config(page_title="IND320 App", layout="wide") 
st.write("Welcome to the Streamlit App for IND320. Use the sidebar to navigate between pages.")
# Load cached data
df = load_data() 

st.subheader("Preview (first 10 rows)")
# Describe the data
st.write("This is a preview of the dataset.")
st.dataframe(df.head(10), use_container_width=True)
st.write(f"Data has {len(df)} rows and {len(df.columns)} columns.")