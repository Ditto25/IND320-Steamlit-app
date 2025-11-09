import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import toml
# Attempt to import STL from statsmodels; if unavailable, set a flag so the app can
# show a clear error message rather than raising an import error during static analysis.
try:
    from statsmodels.tsa.seasonal import STL
    _STL_AVAILABLE = True
except Exception:
    STL = None
    _STL_AVAILABLE = False

# Attempt to import scipy.signal for spectrogram; fall back gracefully if unavailable.
try:
    from scipy import signal
    _SCIPY_AVAILABLE = True
except Exception:
    signal = None
    _SCIPY_AVAILABLE = False

import numpy as np
from functools import lru_cache

# Page configuration: sets the browser tab title and layout behavior
st.set_page_config(
    page_title="Time Series Analysis",
    layout="wide"
)
import streamlit.components.v1 as components

# Collapse the sidebar on load (leaves the sidebar toggle/navigation visible)
components.html(
    """
    <script>
    (function() {
        const tryCollapse = () => {
            const btn = window.parent.document.querySelector('button[aria-label="Toggle sidebar"]');
            const sidebar = window.parent.document.querySelector('div[data-testid="stSidebar"]');
            if (btn && sidebar) {
                const w = parseFloat(window.getComputedStyle(sidebar).width) || 0;
                if (w > 120) {
                    try { btn.click(); } catch(e) {}
                }
                clearInterval(interval);
            }
        };
        const interval = setInterval(tryCollapse, 100);
        setTimeout(() => clearInterval(interval), 3000);
    })();
    </script>
    """,
    height=0,
)

# Fixed (non-editable) displayed text
title_text = "📈 Advanced Time Series Analysis"
header_text = "🌀 STL Decomposition and 📡 Spectrogram Analysis"
description_text = "Analyze electricity production patterns using advanced time series techniques."

stl_intro = (
    "STL decomposes a time series into three components:\n"
    "- Trend: Long-term progression\n"
    "- Seasonal: Repeating patterns (daily, weekly, etc.)\n"
    "- Residual: Remainder after removing trend and seasonal"
)

stl_interpretation = (
    "- Trend: Shows long-term changes in production\n"
    "- Seasonal: Reveals daily/weekly patterns\n"
    "- Residual: Contains irregular variations and noise"
)

spec_intro = (
    "A spectrogram shows how frequency content changes over time, revealing:\n"
    "- Daily cycles: ~1/24 cycles/hour\n"
    "- Weekly patterns: ~1/168 cycles/hour\n"
    "- Seasonal shifts: Long-term frequency changes"
)

spec_key_freq = (
    "- Daily cycle: 0.042 cycles/hour (1/24)\n"
    "- Weekly cycle: 0.006 cycles/hour (1/168)\n"
    "- Brighter colors: Higher power at that frequency/time"
)

# MongoDB connection
@lru_cache(maxsize=1)
def init_connection():
    """Initialize MongoDB connection using secrets.
    Cached in-memory to avoid Streamlit's cache which may access UI components in some environments.
    Expects a 'URI' entry in .streamlit/secrets.toml under [MONGO]."""
    # Load Mongo URI
    secrets = toml.load(".streamlit/secrets.toml")
    uri = secrets["MONGO"]["uri"]

    client = MongoClient(uri, server_api=ServerApi('1'))
    return client

# Load data from MongoDB
@lru_cache(maxsize=1)
def load_production_data():
    """Load production data from MongoDB and parse time columns.
    Returned DataFrame includes 'startTime_parsed' and 'endTime_parsed' as UTC timestamps.
    Cached in-memory to avoid using Streamlit's cache internals which may require UI elements.
    """
    client = init_connection()
    db = client['Database']
    collection = db['data']
    # Fetch all documents from MongoDB
    records = list(collection.find({}, {'_id': 0}))
    if not records:
        raise ValueError("No data found in MongoDB! Please run your notebook to insert data first.")
    df = pd.DataFrame(records)
    # Parse time columns to datetime
    df['startTime_parsed'] = pd.to_datetime(df['startTime'], utc=True)
    df['endTime_parsed'] = pd.to_datetime(df['endTime'], utc=True)
    return df

def stl_analysis(df, price_area, production_group, period=24, seasonal=7, trend=None, robust=False):
    """Perform STL decomposition on a selected subset of the data.
    - df: full DataFrame with parsed times
    - price_area, production_group: filters to select a time series
    - period: primary seasonal period (e.g., 24 for daily if hourly data)
    - seasonal: window length for seasonal smoothing (should be odd)
    - trend: trend smoothing parameter (None lets STL choose)
    - robust: if True, use robust fitting to reduce outlier influence
    Returns a Matplotlib figure with original, trend, seasonal, and residual subplots.
    """
    # If statsmodels' STL is not available, surface a clear error message instead
    if not _STL_AVAILABLE:
        return None, ("STL decomposition is unavailable because statsmodels could not be imported; "
                      "please install statsmodels in your environment (e.g. pip install statsmodels)")

    filtered = df[(df['priceArea'] == price_area) & (df['productionGroup'] == production_group)]
    if len(filtered) == 0:
        return None, "No data available for selected combination"
    filtered = filtered.sort_values('startTime_parsed')
    # Create a time-indexed series; forward/backward fill any missing values
    ts = pd.Series(filtered['quantityKwh'].values, index=filtered['startTime_parsed']).ffill().bfill()
    stl = STL(ts, period=period, seasonal=seasonal, trend=trend, robust=robust)
    result = stl.fit()
    # Build a stacked plot of original, trend, seasonal and residual
    fig, axes = plt.subplots(4, 1, figsize=(15, 10))
    axes[0].plot(ts.index, ts.values, color='black', linewidth=1)
    axes[0].set_ylabel('Original', fontsize=11, fontweight='bold')
    axes[0].set_title(f'STL Decomposition: {production_group} in {price_area}', fontsize=14, fontweight='bold', pad=15)
    axes[0].grid(True, alpha=0.3)
    axes[1].plot(ts.index, result.trend, color='blue', linewidth=1.5); axes[1].set_ylabel('Trend', fontsize=11, fontweight='bold'); axes[1].grid(True, alpha=0.3)
    axes[2].plot(ts.index, result.seasonal, color='green', linewidth=1); axes[2].set_ylabel('Seasonal', fontsize=11, fontweight='bold'); axes[2].grid(True, alpha=0.3)
    axes[3].plot(ts.index, result.resid, color='red', linewidth=1); axes[3].set_ylabel('Residual', fontsize=11, fontweight='bold'); axes[3].set_xlabel('Time', fontsize=12, fontweight='bold'); axes[3].grid(True, alpha=0.3)
    for ax in axes:
        ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    return fig, None

def spectrogram_analysis(df, price_area, production_group, window_length=168, window_overlap=84):
    """Compute and plot a spectrogram for the selected production time series.
    - window_length: number of samples in each FFT window (hours if hourly data)
    - window_overlap: overlap between consecutive windows
    Returns a Matplotlib figure with a time-frequency power plot (dB).
    """
    filtered = df[(df['priceArea'] == price_area) & (df['productionGroup'] == production_group)]
    if len(filtered) == 0:
        return None, "No data available for selected combination"
    filtered = filtered.sort_values('startTime_parsed')
    # Extract the production series, ensure no NaNs
    production = pd.Series(filtered['quantityKwh'].values).ffill().bfill().values

    # Prefer scipy.signal.spectrogram when available, otherwise use a NumPy-based STFT fallback.
    if _SCIPY_AVAILABLE and signal is not None:
        # Compute spectrogram (fs=1.0 means 1 sample per hour if data is hourly)
        frequencies, times, Sxx = signal.spectrogram(production, fs=1.0, window='hann', nperseg=window_length, noverlap=window_overlap)
    else:
        # Fallback STFT implementation using NumPy (returns frequencies, times, Sxx)
        n = len(production)
        nperseg = int(window_length)
        noverlap = int(window_overlap)
        step = max(1, nperseg - noverlap)
        # Need at least one full segment
        if n < 1 or nperseg <= 0:
            return None, "Invalid window settings for spectrogram"
        segments = max(0, (n - noverlap + step - 1) // step)
        if segments <= 0:
            return None, "Not enough data for selected window/overlap settings"
        # Frequencies for real FFT
        frequencies = np.fft.rfftfreq(nperseg, d=1.0)
        times = (np.arange(segments) * step).astype(float)  # hours from start (fs=1)
        Sxx = np.empty((len(frequencies), segments), dtype=float)
        window = np.hanning(nperseg)
        win_norm = np.sum(window ** 2)
        for i in range(segments):
            start = i * step
            seg = production[start:start + nperseg]
            if len(seg) < nperseg:
                seg = np.pad(seg, (0, nperseg - len(seg)), 'constant')
            fft = np.fft.rfft(seg * window)
            Sxx[:, i] = (np.abs(fft) ** 2) / (win_norm + 1e-16)

    # Convert power to decibels for plotting
    Sxx_db = 10 * np.log10(Sxx + 1e-10)
    fig, ax = plt.subplots(figsize=(15, 8))
    im = ax.pcolormesh(times, frequencies, Sxx_db, shading='gouraud', cmap='viridis')
    plt.colorbar(im, ax=ax, label='Power (dB)')
    ax.set_xlabel('Time (hours from start)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Frequency (cycles/hour)', fontsize=12, fontweight='bold')
    ax.set_title(f'Spectrogram: {production_group} Production in {price_area}\nWindow: {window_length}h, Overlap: {window_overlap}h', fontsize=14, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3, color='white', linewidth=0.5)
    plt.tight_layout()
    return fig, None

# Main page content using fixed text
st.title(title_text)          # Top-level title (fixed)
st.header(header_text)        # Subtitle/header (fixed)
st.markdown(description_text) # Introductory description (fixed)
st.markdown("---")

try:
    df = load_production_data()
    # Available options for selection widgets derived from the dataset
    price_areas = sorted(df['priceArea'].unique())
    production_groups = sorted(df['productionGroup'].unique())
    tab1, tab2 = st.tabs(["📊 STL Decomposition", "🎵 Spectrogram"])

    with tab1:
        st.subheader("Seasonal-Trend Decomposition using LOESS (STL)")
        st.markdown(stl_intro)  # Show the STL introduction text

        # Inputs for STL analysis
        col1, col2, col3 = st.columns(3)
        with col1:
            # Select which geographical price area to analyze
            stl_price_area = st.selectbox("Price Area", options=price_areas, key="stl_area")
        with col2:
            # Select which production group (e.g., solar, wind, thermal)
            stl_prod_group = st.selectbox("Production Group", options=production_groups, key="stl_group")
        with col3:
            # Seasonal period input (default 24 for daily cycle in hourly data)
            stl_period = st.number_input("Seasonal Period", min_value=2, max_value=720, value=24, help="Length of seasonal cycle (24=daily, 168=weekly)")
        col4, col5, col6 = st.columns(3)
        with col4:
            # Seasonal smoothing window length for STL (must be odd)
            stl_seasonal = st.slider("Seasonal Smoothing", min_value=3, max_value=25, value=7, step=2, help="Higher = smoother seasonal component (must be odd)")
        with col5:
            # Toggle robust fitting to reduce sensitivity to outliers
            stl_robust = st.checkbox("Robust Fitting", value=True, help="Resistant to outliers")
        # Ensure seasonal window is odd (STL requirement)
        if stl_seasonal % 2 == 0:
            stl_seasonal += 1
        # Button to trigger the STL decomposition
        if st.button("Run STL Analysis", key="stl_button"):
            with st.spinner("Performing STL decomposition..."):
                fig, error = stl_analysis(df, stl_price_area, stl_prod_group, period=stl_period, seasonal=stl_seasonal, robust=stl_robust)
                if error:
                    st.error(error)
                else:
                    st.pyplot(fig)
                    st.markdown("---")
                    st.info(stl_interpretation)  # Show interpretation tips

    with tab2:
        st.subheader("Spectrogram - Frequency-Time Analysis")
        st.markdown(spec_intro)  # Show spectrogram introduction
        col1, col2 = st.columns(2)
        with col1:
            # Select price area for spectrogram
            spec_price_area = st.selectbox("Price Area", options=price_areas, key="spec_area")
        with col2:
            # Select production group for spectrogram
            spec_prod_group = st.selectbox("Production Group", options=production_groups, key="spec_group")
        col3, col4 = st.columns(2)
        with col3:
            # Window length in hours for the FFT segments used by spectrogram
            spec_window = st.slider("Window Length (hours)", min_value=24, max_value=720, value=168, step=24, help="Larger = better frequency resolution")
        with col4:
            # Overlap between windows; higher overlap smooths the spectrogram in time
            spec_overlap = st.slider("Window Overlap (hours)", min_value=0, max_value=int(spec_window * 0.9), value=int(spec_window * 0.5), step=12, help="Higher = smoother spectrogram")
        # Button to compute and display spectrogram
        if st.button("Create Spectrogram", key="spec_button"):
            with st.spinner("Computing spectrogram..."):
                fig, error = spectrogram_analysis(df, spec_price_area, spec_prod_group, window_length=spec_window, window_overlap=spec_overlap)
                if error:
                    st.error(error)
                else:
                    st.pyplot(fig)
                    st.markdown("---")
                    st.info(spec_key_freq)  # Show key frequency tips

except Exception as e:
    # Generic error handling to surface issues to the user
    st.error(f"An error occurred: {str(e)}")
    st.exception(e)
