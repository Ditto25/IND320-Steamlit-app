# IND320-Streamlit-app
Mandatory assignment IND320

## CSV Data Analysis Notebook

This repository contains a comprehensive Jupyter Notebook for CSV data analysis and visualization.

### Files Included

- `csv_analysis.ipynb` - Main Jupyter Notebook with complete analysis
- `sample_data.csv` - Sample dataset for demonstration
- `requirements.txt` - Python dependencies
- `test_functionality.py` - Validation script for testing functionality

### Features

The notebook demonstrates:

1. **CSV File Reading** - Loading data with Pandas
2. **Data Exploration** - Comprehensive dataset overview
3. **Individual Column Visualization** - Separate plots for each column
4. **Multi-Scale Visualization** - Multiple approaches for combining columns with different scales:
   - Normalized plots (0-1 scale)
   - Standardized plots (z-score)
   - Multiple y-axes plots
   - Correlation heatmap
5. **Documentation** - Complete development log and AI integration notes

### Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the validation test:
   ```bash
   python test_functionality.py
   ```

3. Start Jupyter Notebook:
   ```bash
   jupyter notebook csv_analysis.ipynb
   ```

### Dataset

The sample dataset includes:
- Date (time series data)
- Temperature (°C)
- Humidity (%)
- Pressure (hPa)
- Sales (units)
- Population (count)

These variables have different scales, demonstrating the multi-scale visualization techniques.

### Visualization Approaches

The notebook addresses the challenge of plotting variables with different scales through:

1. **Normalization** - Scales all values to [0,1] range
2. **Standardization** - Centers data with mean=0, std=1
3. **Multiple Y-axes** - Preserves original scales
4. **Correlation Analysis** - Shows relationships between variables

### Requirements

- Python 3.7+
- pandas >= 2.0.0
- matplotlib >= 3.7.0
- seaborn >= 0.12.0
- numpy >= 1.24.0
- scikit-learn >= 1.3.0
- jupyter >= 1.0.0
