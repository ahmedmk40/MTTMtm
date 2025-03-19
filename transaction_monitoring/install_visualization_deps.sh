#!/bin/bash

# Install dependencies for visualizations
echo "Installing dependencies for visualizations..."

# Install matplotlib, seaborn, and pandas
pip install matplotlib seaborn pandas

# Install SHAP for model explainability
pip install shap

# Install plotly for Sankey diagrams
pip install plotly kaleido

echo "Dependencies installed successfully!"